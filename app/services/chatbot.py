import logging
import os
import pickle
import tempfile
from typing import List, Dict, Optional

import boto3
from botocore.exceptions import ClientError
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
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

        # Initialize S3 client for vector store caching
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
        )

        # Vector store for RAG (will be created per research paper)
        self.vector_store = None
        self.research_context = None

        # Conversation history: Dict[research_id, List[Dict[role, content]]]
        # Format: {research_id: [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
        self.conversation_history: Dict[int, List[Dict[str, str]]] = {}

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

        logger.info(f"Downloading PDF from S3: s3://{settings.S3_BUCKET}/{object_key}")

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

    def _get_vector_store_s3_key(self, research_id: int) -> str:
        """Generate S3 key for vector store cache"""
        return f"vector_stores/research_{research_id}/faiss_index"

    def _get_conversation_history_s3_key(self, research_id: int) -> str:
        """Generate S3 key for conversation history cache"""
        return f"conversation_history/research_{research_id}/history.pkl"

    def _save_vector_store_to_s3(self, vector_store: FAISS, research_id: int):
        """
        Save FAISS vector store to S3 for caching

        This reduces costs and improves performance by avoiding regeneration
        of vector embeddings on each request.
        """
        try:
            # Create temporary directory for FAISS index
            with tempfile.TemporaryDirectory() as tmp_dir:
                index_path = os.path.join(tmp_dir, "faiss_index")

                # Save FAISS index locally
                vector_store.save_local(index_path)

                # Upload all FAISS files to S3
                s3_base_key = self._get_vector_store_s3_key(research_id)

                for file_name in os.listdir(index_path):
                    file_path = os.path.join(index_path, file_name)
                    s3_key = f"{s3_base_key}/{file_name}"

                    self.s3_client.upload_file(file_path, settings.S3_BUCKET, s3_key)
                    logger.info(f"Uploaded vector store file to S3: {s3_key}")

                logger.info(f"Vector store saved to S3 for research_id: {research_id}")

        except Exception as e:
            logger.warning(f"Failed to save vector store to S3: {e}")
            # Don't raise - caching is optional, continue without it

    def _load_vector_store_from_s3(self, research_id: int) -> Optional[FAISS]:
        """
        Load FAISS vector store from S3 cache

        Returns:
            FAISS vector store if found in cache, None otherwise
        """
        try:
            s3_base_key = self._get_vector_store_s3_key(research_id)

            # List all files in the vector store directory
            response = self.s3_client.list_objects_v2(
                Bucket=settings.S3_BUCKET,
                Prefix=s3_base_key
            )

            if 'Contents' not in response:
                logger.info(f"No cached vector store found for research_id: {research_id}")
                return None

            # Create temporary directory to download FAISS index
            with tempfile.TemporaryDirectory() as tmp_dir:
                index_path = os.path.join(tmp_dir, "faiss_index")
                os.makedirs(index_path, exist_ok=True)

                # Download all FAISS files from S3
                for obj in response['Contents']:
                    s3_key = obj['Key']
                    file_name = os.path.basename(s3_key)
                    file_path = os.path.join(index_path, file_name)

                    self.s3_client.download_file(settings.S3_BUCKET, s3_key, file_path)
                    logger.info(f"Downloaded vector store file from S3: {s3_key}")

                # Load FAISS index
                vector_store = FAISS.load_local(
                    index_path,
                    self.embeddings,
                    allow_dangerous_deserialization=True
                )

                logger.info(f"Vector store loaded from S3 cache for research_id: {research_id}")
                return vector_store

        except Exception as e:
            logger.warning(f"Failed to load vector store from S3: {e}")
            return None

    def _save_conversation_history_to_s3(self, research_id: int):
        """
        Save conversation history to S3 for persistence

        This allows conversation history to persist across service restarts
        and be shared across multiple instances.
        """
        try:
            history = self.conversation_history.get(research_id, [])

            if not history:
                logger.info(f"No conversation history to save for research_id: {research_id}")
                return

            # Create temporary file for history
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pkl') as tmp:
                pickle.dump(history, tmp)
                tmp.flush()

                # Upload to S3
                s3_key = self._get_conversation_history_s3_key(research_id)
                self.s3_client.upload_file(tmp.name, settings.S3_BUCKET, s3_key)

                # Clean up
                os.unlink(tmp.name)

                logger.info(f"Conversation history saved to S3 for research_id: {research_id} ({len(history)} messages)")

        except Exception as e:
            logger.warning(f"Failed to save conversation history to S3: {e}")
            # Don't raise - saving history is optional, continue without it

    def _load_conversation_history_from_s3(self, research_id: int) -> List[Dict[str, str]]:
        """
        Load conversation history from S3 cache

        Returns:
            List of conversation messages if found in cache, empty list otherwise
        """
        try:
            s3_key = self._get_conversation_history_s3_key(research_id)

            # Check if history exists in S3
            try:
                self.s3_client.head_object(Bucket=settings.S3_BUCKET, Key=s3_key)
            except ClientError as e:
                error_code = e.response.get("Error", {}).get("Code", "")
                if error_code == "404":
                    logger.info(f"No cached conversation history found for research_id: {research_id}")
                    return []
                raise

            # Download history from S3
            with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.pkl') as tmp:
                self.s3_client.download_file(settings.S3_BUCKET, s3_key, tmp.name)
                tmp.close()

                # Load history
                with open(tmp.name, 'rb') as f:
                    history = pickle.load(f)

                # Clean up
                os.unlink(tmp.name)

                logger.info(f"Conversation history loaded from S3 for research_id: {research_id} ({len(history)} messages)")
                return history

        except Exception as e:
            logger.warning(f"Failed to load conversation history from S3: {e}")
            return []

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
        """Generate a brief summary with greeting for RAG chatbot"""
        try:
            # Combine first few pages for context
            context_text = "\n".join(
                [doc.page_content for doc in documents[:3]]
            )  # First 3 pages

            # Create prompt for summarization with greeting
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a research assistant. Provide a friendly greeting and a brief 1-2 sentence summary of this research paper in Korean. Start with a greeting like '안녕하세요!' and mention that the RAG chatbot is ready.",
                    ),
                    ("user", "{content}"),
                ]
            )

            # Generate summary with greeting
            chain = prompt | self.llm
            result = chain.invoke({"content": context_text})

            return result.content.strip()

        except Exception as e:
            logger.error(f"Failed to generate context summary: {e}")
            raise Exception(f"논문 요약 생성 중 오류가 발생했습니다: {str(e)}")

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

            return {"title": research.title, "answer": context_summary}

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

    def _get_conversation_history(self, research_id: int) -> List[Dict[str, str]]:
        """Get conversation history for a specific research"""
        return self.conversation_history.get(research_id, [])

    def _add_to_conversation_history(
        self, research_id: int, role: str, content: str
    ):
        """Add a message to conversation history"""
        if research_id not in self.conversation_history:
            self.conversation_history[research_id] = []

        self.conversation_history[research_id].append(
            {"role": role, "content": content}
        )

        # Limit history to last 10 messages (5 exchanges) to control token usage
        if len(self.conversation_history[research_id]) > 10:
            self.conversation_history[research_id] = self.conversation_history[
                research_id
            ][-10:]

    def _build_prompt_with_history(
        self,
        title: str,
        abstract: str,
        context: str,
        question: str,
        history: List[Dict[str, str]],
    ) -> ChatPromptTemplate:
        """Build prompt template with conversation history"""

        messages = [
            (
                "system",
                """You are a helpful research assistant. Answer the user's question based on the provided research paper context and conversation history.

Research Title: {title}
Abstract: {abstract}

Guidelines:
- Answer in Korean (한국어로 답변하세요)
- Use the provided context to answer accurately
- Consider the conversation history to provide coherent responses
- If the answer is not in the context, say so honestly
- Cite specific parts of the research when relevant
- Be clear and concise

Context from research paper:
{context}""",
            )
        ]

        # Add conversation history
        for msg in history:
            if msg["role"] == "user":
                messages.append(("user", msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(("assistant", msg["content"]))

        # Add current question
        messages.append(("user", "{question}"))

        return ChatPromptTemplate.from_messages(messages)

    def chat_with_research(
        self, research_id: int, question: str, top_k: int = 4
    ) -> dict:
        """
        Stateful chat method with vector store caching and conversation history

        This method:
        1. Tries to load cached vector store from S3
        2. If not cached, creates vector store and saves to S3
        3. Maintains conversation history for context-aware responses
        4. Uses RAG to answer questions based on research content

        Args:
            research_id: ID of the research to chat about
            question: User's question
            top_k: Number of relevant chunks to retrieve

        Returns:
            Chatbot response based on research context and conversation history
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

            # 3. Try to load vector store from S3 cache
            logger.info(f"Attempting to load vector store from S3 cache for research_id: {research_id}")
            vector_store = self._load_vector_store_from_s3(research_id)

            # 4. If not cached, create new vector store and save to S3
            if vector_store is None:
                logger.info("Cache miss - creating new vector store")

                # Load PDF from S3
                logger.info(f"Loading PDF from S3: {research.object_key}")
                documents = self._load_pdf_from_s3(research.object_key)

                if not documents:
                    raise ValueError("Failed to load PDF content from S3")

                # Create vector store
                logger.info("Creating vector store for RAG")
                vector_store = self._create_vector_store(documents)

                # Save to S3 for future use
                self._save_vector_store_to_s3(vector_store, research_id)
            else:
                logger.info("Cache hit - using cached vector store from S3")

            # 5. Retrieve relevant documents using similarity search
            logger.info(
                f"Searching for relevant context for question: {question[:50]}..."
            )
            relevant_docs = vector_store.similarity_search(question, k=top_k)

            # 6. Combine retrieved context
            context = "\n\n".join([doc.page_content for doc in relevant_docs])

            # 7. Load conversation history from S3 if not in memory
            if research_id not in self.conversation_history:
                logger.info(f"Loading conversation history from S3 for research_id: {research_id}")
                s3_history = self._load_conversation_history_from_s3(research_id)
                if s3_history:
                    self.conversation_history[research_id] = s3_history
                    logger.info(f"Loaded {len(s3_history)} messages from S3")

            # 8. Get conversation history
            history = self._get_conversation_history(research_id)

            # 9. Create prompt with context and history
            prompt = self._build_prompt_with_history(
                title=research.title,
                abstract=research.abstract or "No abstract available",
                context=context,
                question=question,
                history=history,
            )

            # 10. Generate response using LLM
            chain = prompt | self.llm
            result = chain.invoke(
                {
                    "title": research.title,
                    "abstract": research.abstract or "No abstract available",
                    "context": context,
                    "question": question,
                }
            )

            answer = result.content.strip()

            # 11. Save to conversation history (in-memory)
            self._add_to_conversation_history(research_id, "user", question)
            self._add_to_conversation_history(research_id, "assistant", answer)

            # 12. Save conversation history to S3 for persistence
            self._save_conversation_history_to_s3(research_id)

            logger.info("Generated chatbot response successfully")

            return {"title": research.title, "answer": answer}

        except FileNotFoundError as e:
            logger.error(f"Research not found: {e}")
            raise e
        except ValueError as e:
            logger.error(f"Invalid research data: {e}")
            raise e
        except Exception as e:
            logger.error(f"Chat with research failed: {e}")
            raise Exception(f"대화 중 오류가 발생했습니다: {str(e)}")

    # ============================================================================
    # DANGER ZONE: 캐시 및 이력 저장 관리 영역
    # ============================================================================
    # 다음 메서드는 캐시 데이터와 대화 이력을 수정 또는 삭제합니다.
    # ============================================================================

    def clear_conversation_history(self, research_id: int) -> dict:
        """
        ⚠️ WARNING: Clear conversation history for a specific research

        This will DELETE all conversation history for the specified research
        both from memory and S3.
        This operation is IRREVERSIBLE.

        Use cases:
        - User wants to start a fresh conversation
        - Conversation context is no longer relevant
        - Memory usage optimization

        Args:
            research_id: ID of the research to clear history for

        Returns:
            dict with status message
        """
        message_count = 0

        # Clear from memory
        if research_id in self.conversation_history:
            message_count = len(self.conversation_history[research_id])
            del self.conversation_history[research_id]
            logger.warning(
                f"⚠️ Cleared {message_count} messages from in-memory conversation history for research_id: {research_id}"
            )

        # Delete from S3
        try:
            s3_key = self._get_conversation_history_s3_key(research_id)
            self.s3_client.delete_object(Bucket=settings.S3_BUCKET, Key=s3_key)
            logger.warning(f"⚠️ Deleted conversation history from S3 for research_id: {research_id}")
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "404":
                logger.info(f"No conversation history found in S3 for research_id: {research_id}")
            else:
                logger.warning(f"Failed to delete conversation history from S3: {e}")

        if message_count > 0:
            return {
                "status": "success",
                "message": f"대화 이력이 삭제되었습니다 ({message_count}개 메시지)",
            }
        else:
            return {
                "status": "success",
                "message": "삭제할 대화 이력이 없습니다",
            }

    def refresh_vector_store_cache(self, research_id: int) -> dict:
        """
        ⚠️ DANGER: Delete and regenerate vector store cache for a research

        This will:
        1. DELETE the cached vector store from S3
        2. CLEAR the conversation history for this research
        3. Force regeneration of vector store on next chat request

        This operation is IRREVERSIBLE and should only be used when:
        - The research PDF has been updated
        - The vector store is corrupted
        - Embedding model has changed
        - You want to free up S3 storage

        COST WARNING: Regenerating vector stores incurs embedding API costs!

        Args:
            research_id: ID of the research to refresh cache for

        Returns:
            dict with status message
        """
        try:
            # 1. Validate research exists
            research = self.research_repository.get_by_id(research_id)
            if not research:
                raise FileNotFoundError(f"Research with ID {research_id} not found")

            # 2. Delete vector store from S3
            s3_base_key = self._get_vector_store_s3_key(research_id)

            # List all files in the vector store directory
            response = self.s3_client.list_objects_v2(
                Bucket=settings.S3_BUCKET, Prefix=s3_base_key
            )

            if "Contents" in response:
                # Delete all files
                objects_to_delete = [{"Key": obj["Key"]} for obj in response["Contents"]]
                self.s3_client.delete_objects(
                    Bucket=settings.S3_BUCKET, Delete={"Objects": objects_to_delete}
                )
                logger.warning(
                    f"⚠️ DELETED {len(objects_to_delete)} vector store files from S3 for research_id: {research_id}"
                )
                cache_deleted = True
            else:
                logger.info(f"No cached vector store found in S3 for research_id: {research_id}")
                cache_deleted = False

            # 3. Clear conversation history
            history_result = self.clear_conversation_history(research_id)

            logger.warning(
                f"⚠️ REFRESH COMPLETED for research_id: {research_id} - "
                f"Cache deleted: {cache_deleted}, History cleared: {history_result['status']}"
            )

            return {
                "status": "success",
                "message": f"캐시가 삭제되었습니다. 다음 대화 시 벡터 스토어가 재생성됩니다.",
                "cache_deleted": cache_deleted,
                "history_cleared": history_result["status"] == "success",
            }

        except FileNotFoundError as e:
            logger.error(f"Research not found: {e}")
            raise e
        except Exception as e:
            logger.error(f"Failed to refresh vector store cache: {e}")
            raise Exception(f"캐시 삭제 중 오류가 발생했습니다: {str(e)}")

