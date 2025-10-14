import logging
import os
import tempfile

import boto3
from botocore.exceptions import ClientError
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.research_repository import ResearchRepository

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChatbotService:
    def __init__(self, db: Session):
        self.db = db
        self.research_repository = ResearchRepository(db)

        # Initialize Azure OpenAI LLM
        self.llm = AzureChatOpenAI(
            openai_api_version="2024-02-01",
            azure_deployment=settings.AOAI_DEPLOY_GPT4O,
            temperature=0.7,
            api_key=settings.AOAI_API_KEY,
            azure_endpoint=settings.AOAI_ENDPOINT,
        )

        # Initialize embeddings
        self.embeddings = AzureOpenAIEmbeddings(
            openai_api_version="2024-02-01",
            azure_deployment=settings.AOAI_DEPLOY_EMBED_3_SMALL,
            api_key=settings.AOAI_API_KEY,
            azure_endpoint=settings.AOAI_ENDPOINT,
        )

        # Vector store for RAG (will be created per research paper)
        self.vector_store = None
        self.research_context = None

    def _load_pdf_from_s3(self, object_key: str):
        """Load PDF file from S3 bucket using object_key"""
        # Validate S3 configuration
        if not settings.S3_BUCKET:
            raise ValueError(
                "S3_BUCKET environment variable is not configured. "
                "Please set S3_BUCKET in your environment variables."
            )
        if not settings.AWS_ACCESS_KEY or not settings.AWS_SECRET_KEY:
            raise ValueError(
                "AWS credentials are not configured. "
                "Please set AWS_ACCESS_KEY and AWS_SECRET_KEY in your environment variables."
            )

        logger.info(
            f"Downloading PDF from S3: s3://{settings.S3_BUCKET}/{object_key}"
        )

        # Initialize S3 client
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
        )

        try:
            # Check if file exists in S3
            s3_client.head_object(Bucket=settings.S3_BUCKET, Key=object_key)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                raise FileNotFoundError(
                    f"PDF file not found in S3 bucket. "
                    f"Expected location: s3://{settings.S3_BUCKET}/{object_key}"
                )
            else:
                raise ValueError(f"Error accessing S3 file: {str(e)}")

        # Download PDF from S3 to temporary file
        try:
            # Create temporary file
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

            # Download from S3
            s3_client.download_fileobj(settings.S3_BUCKET, object_key, tmp)
            tmp.flush()
            tmp.close()

            logger.info("PDF downloaded successfully from S3")

            # Load PDF using PyMuPDFLoader
            loader = PyMuPDFLoader(tmp.name)
            docs = loader.load()

            # Clean up temporary file
            os.unlink(tmp.name)

            return docs

        except Exception as e:
            # Clean up temporary file if it exists
            if tmp and os.path.exists(tmp.name):
                os.unlink(tmp.name)
            raise ValueError(f"Failed to download or load PDF from S3: {str(e)}")

    def _create_vector_store(self, documents):
        """Create FAISS vector store from documents for RAG"""
        try:
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200,
                length_function=len,
            )
            splits = text_splitter.split_documents(documents)

            logger.info(f"Created {len(splits)} document chunks for vector store")

            # Create FAISS vector store
            vector_store = FAISS.from_documents(splits, self.embeddings)

            logger.info("Vector store created successfully")
            return vector_store

        except Exception as e:
            raise ValueError(f"Failed to create vector store: {str(e)}")

    def _generate_context_summary(self, documents):
        """Generate a brief summary of the research context"""
        try:
            # Combine first few pages for context
            context_text = "\n".join(
                [doc.page_content for doc in documents[:3]]
            )  # First 3 pages

            # Create prompt for summarization
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a research assistant. Provide a brief 2-3 sentence summary of this research paper in Korean.",
                    ),
                    ("user", "{content}"),
                ]
            )

            # Generate summary
            chain = prompt | self.llm
            result = chain.invoke({"content": context_text})

            return result.content.strip()

        except Exception as e:
            logger.warning(f"Failed to generate context summary: {e}")
            return "연구 논문의 내용을 기반으로 대화할 준비가 되었습니다."

    def create_chatbot_from_research_id(self, research_id: int) -> dict:
        """
        Validate research exists and has PDF file available

        This method:
        1. Fetches research from database
        2. Validates research has object_key (PDF file)
        3. Loads PDF and generates context summary
        4. Returns chatbot response with context summary
        """
        try:
            # 1. Fetch research from database
            logger.info(f"Fetching research with ID: {research_id}")
            research = self.research_repository.get_by_id(research_id)

            if not research:
                raise FileNotFoundError(f"Research with ID {research_id} not found")

            # 2. Validate research has object_key (S3 path)
            if not research.object_key:
                raise ValueError(
                    f"Research with ID {research_id} does not have an associated PDF file. "
                    f"Please download the PDF first using /research/download/{research_id}"
                )

            # 3. Load PDF from S3 for summary generation
            logger.info(f"Loading PDF from S3: {research.object_key}")
            documents = self._load_pdf_from_s3(research.object_key)

            if not documents:
                raise ValueError("Failed to load PDF content from S3")

            # 4. Generate context summary
            logger.info("Generating context summary")
            context_summary = self._generate_context_summary(documents)

            logger.info(
                f"Chatbot validated successfully for research ID: {research_id}"
            )

            return {
                "title": research.title,
                "answer": context_summary
            }

        except FileNotFoundError as e:
            logger.error(f"Research not found: {e}")
            raise e
        except ValueError as e:
            logger.error(f"Invalid research data: {e}")
            raise e
        except Exception as e:
            logger.error(f"Chatbot creation failed: {e}")
            raise Exception(f"챗봇 생성 중 오류가 발생했습니다: {str(e)}")

    def chat(self, question: str, top_k: int = 4) -> str:
        """
        Chat with the loaded research paper using RAG

        Args:
            question: User's question
            top_k: Number of relevant chunks to retrieve

        Returns:
            Chatbot response based on research context
        """
        try:
            if not self.vector_store:
                raise ValueError(
                    "Chatbot not initialized. Please create chatbot context first using create_chatbot_from_research_id"
                )

            # 1. Retrieve relevant documents using similarity search
            logger.info(
                f"Searching for relevant context for question: {question[:50]}..."
            )
            relevant_docs = self.vector_store.similarity_search(question, k=top_k)

            # 2. Combine retrieved context
            context = "\n\n".join([doc.page_content for doc in relevant_docs])

            # 3. Create prompt with context
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a helpful research assistant. Answer the user's question based on the provided research paper context.

Research Title: {title}
Abstract: {abstract}

Guidelines:
- Answer in Korean (한국어로 답변하세요)
- Use the provided context to answer accurately
- If the answer is not in the context, say so honestly
- Cite specific parts of the research when relevant
- Be clear and concise

Context from research paper:
{context}""",
                    ),
                    ("user", "{question}"),
                ]
            )

            # 4. Generate response using LLM
            chain = prompt | self.llm
            result = chain.invoke(
                {
                    "title": self.research_context.get("title", "Unknown"),
                    "abstract": self.research_context.get(
                        "abstract", "No abstract available"
                    ),
                    "context": context,
                    "question": question,
                }
            )

            logger.info("Generated chatbot response successfully")
            return result.content.strip()

        except ValueError as e:
            logger.error(f"Chat failed: {e}")
            raise e
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise Exception(f"대화 중 오류가 발생했습니다: {str(e)}")

    def chat_with_research(self, research_id: int, question: str, top_k: int = 4) -> dict:
        """
        Stateless chat method that loads research, creates vector store, and answers question

        This method is designed to be called from an API endpoint without session management.
        It recreates the RAG context on each request.

        Args:
            research_id: ID of the research to chat about
            question: User's question
            top_k: Number of relevant chunks to retrieve

        Returns:
            Chatbot response based on research context
        """
        try:
            # 1. Fetch research from database
            logger.info(f"Fetching research with ID: {research_id}")
            research = self.research_repository.get_by_id(research_id)

            if not research:
                raise FileNotFoundError(f"Research with ID {research_id} not found")

            # 2. Validate research has object_key (S3 path)
            if not research.object_key:
                raise ValueError(
                    f"Research with ID {research_id} does not have an associated PDF file. "
                    f"Please download the PDF first using /research/download/{research_id}"
                )

            # 3. Load PDF from S3
            logger.info(f"Loading PDF from S3: {research.object_key}")
            documents = self._load_pdf_from_s3(research.object_key)

            if not documents:
                raise ValueError("Failed to load PDF content from S3")

            # 4. Create vector store for RAG
            logger.info("Creating vector store for RAG")
            vector_store = self._create_vector_store(documents)

            # 5. Retrieve relevant documents using similarity search
            logger.info(
                f"Searching for relevant context for question: {question[:50]}..."
            )
            relevant_docs = vector_store.similarity_search(question, k=top_k)

            # 6. Combine retrieved context
            context = "\n\n".join([doc.page_content for doc in relevant_docs])

            # 7. Create prompt with context
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a helpful research assistant. Answer the user's question based on the provided research paper context.

Research Title: {title}
Abstract: {abstract}

Guidelines:
- Answer in Korean (한국어로 답변하세요)
- Use the provided context to answer accurately
- If the answer is not in the context, say so honestly
- Cite specific parts of the research when relevant
- Be clear and concise

Context from research paper:
{context}""",
                    ),
                    ("user", "{question}"),
                ]
            )

            # 8. Generate response using LLM
            chain = prompt | self.llm
            result = chain.invoke(
                {
                    "title": research.title,
                    "abstract": research.abstract or "No abstract available",
                    "context": context,
                    "question": question,
                }
            )

            logger.info("Generated chatbot response successfully")

            return {
                "title": research.title,
                "answer": result.content.strip()
            }

        except FileNotFoundError as e:
            logger.error(f"Research not found: {e}")
            raise e
        except ValueError as e:
            logger.error(f"Invalid research data: {e}")
            raise e
        except Exception as e:
            logger.error(f"Chat with research failed: {e}")
            raise Exception(f"대화 중 오류가 발생했습니다: {str(e)}")
