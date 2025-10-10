import os
import re
import tempfile
from typing import List

import requests
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.config import settings
from app.schemas.quiz import QuestionResponse, QuizCreate, QuizResponse


class QuizService:
    def __init__(self):
        self.llm_mini = self._get_llm(temperature=0.2, use_mini=True)
        self.embeddings = self._get_embeddings()

    def _get_llm(self, temperature: float = 0.2, use_mini: bool = True):
        """Get Azure OpenAI LLM instance"""
        return AzureChatOpenAI(
            openai_api_version="2024-02-01",
            azure_deployment=(
                settings.AOAI_DEPLOY_GPT4O_MINI
                if use_mini
                else settings.AOAI_DEPLOY_GPT4O
            ),
            temperature=temperature,
            api_key=settings.AOAI_API_KEY,
            azure_endpoint=settings.AOAI_ENDPOINT,
        )

    def _get_embeddings(self):
        """Get Azure OpenAI embeddings instance"""
        return AzureOpenAIEmbeddings(
            model=settings.AOAI_DEPLOY_EMBED_3_LARGE,
            openai_api_version="2024-02-01",
            api_key=settings.AOAI_API_KEY,
            azure_endpoint=settings.AOAI_ENDPOINT,
        )

    def _load_pdf(self, path_or_url: str):
        """Load PDF from local path or URL"""
        if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
            resp = requests.get(path_or_url, timeout=30)
            resp.raise_for_status()
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tmp.write(resp.content)
            tmp.flush()
            loader = PyMuPDFLoader(tmp.name)
            docs = loader.load()
            os.unlink(tmp.name)
        else:
            # Check if file exists
            if not os.path.exists(path_or_url):
                raise FileNotFoundError(f"PDF file not found: {path_or_url}")
            loader = PyMuPDFLoader(path_or_url)
            docs = loader.load()
        return docs

    def _build_vectorstore(self, docs, chunk_size=1000, chunk_overlap=200):
        """Build FAISS vectorstore from documents"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        splits = splitter.split_documents(docs)

        # Add metadata prefix to each chunk
        for d in splits:
            page = d.metadata.get("page", None)
            src = d.metadata.get("source", "")
            prefix = f"[source: {os.path.basename(src)} | page: {page}] "
            d.page_content = prefix + d.page_content

        vs = FAISS.from_documents(splits, self.embeddings)
        return vs

    def _generate_quiz(self, vectorstore):
        """Generate quiz from vectorstore"""
        chunks = vectorstore.similarity_search(
            "Generate exam questions based on this document", k=10
        )
        document_content = "\n\n".join([c.page_content for c in chunks])

        quiz_prompt = """
당신은 논문 기반 O/X 퀴즈 제작자입니다. 아래 문서를 참고하여 한국어 O/X 퀴즈를 만들어 주세요.

조건은 다음과 같습니다:
- 총 다섯 문항을 만들고, 모두 O/X 퀴즈로 구성합니다.
- 각 문항은 참(O) 또는 거짓(X)으로 답할 수 있는 진술문 형태로 작성합니다.
- 각 문항에 대해 정답(O 또는 X)과 해설을 함께 작성합니다.
- 제공할 문제의 경우에는, 논문의 저자 및 작성 시기 등과 같이 지엽적인 부분은 피하세요.
- 기술과 AI 및 논문의 핵심 내용을 기반으로 문제를 생성합니다.
- O와 X 문제의 비율을 적절히 섞어주세요 (예: 3개 O, 2개 X 또는 2개 O, 3개 X).
- 마지막에는 생각해볼 의견 세 가지와 실무 적용 방향 세 가지를 제시합니다.

응답 형식:
각 문제는 다음과 같은 형식으로 작성해주세요:

문제 1: [O 또는 X로 답할 수 있는 진술문]
정답: O (또는 X)
해설: [정답에 대한 설명]

문제 2: [O 또는 X로 답할 수 있는 진술문]
정답: X (또는 O)
해설: [정답에 대한 설명]

... (총 5문제)

생각해볼 의견:
1. [의견 1]
2. [의견 2]
3. [의견 3]

실무 적용 방향:
1. [적용 방향 1]
2. [적용 방향 2]
3. [적용 방향 3]

문서 내용은 다음과 같습니다:
{document_content}

O/X 퀴즈를 작성해 주세요.
"""
        prompt_template = PromptTemplate.from_template(quiz_prompt)
        quiz_chain = prompt_template | self.llm_mini | StrOutputParser()
        quiz_text = quiz_chain.invoke({"document_content": document_content})
        return quiz_text

    def _parse_quiz_response(self, quiz_text: str) -> List[QuestionResponse]:
        """Parse the quiz text into structured QuestionResponse objects"""
        questions = []

        # Split by "문제 " pattern to find individual questions
        question_blocks = re.split(r"문제\s+\d+:", quiz_text)

        for block in question_blocks[1:]:  # Skip the first empty split
            if not block.strip():
                continue

            # Extract question, answer, and explanation
            lines = block.strip().split("\n")
            question_text = ""
            answer_text = ""
            explanation_text = ""

            current_section = "question"

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if line.startswith("정답:"):
                    current_section = "answer"
                    answer_text = line.replace("정답:", "").strip()
                elif line.startswith("해설:"):
                    current_section = "explanation"
                    explanation_text = line.replace("해설:", "").strip()
                elif line.startswith("생각해볼 의견:") or line.startswith(
                    "실무 적용 방향:"
                ):
                    break  # Stop parsing when we reach the end sections
                else:
                    if current_section == "question":
                        question_text += line + " "
                    elif current_section == "answer" and not answer_text:
                        answer_text = line
                    elif current_section == "explanation":
                        explanation_text += line + " "

            # Clean up texts
            question_text = question_text.strip()
            answer_text = answer_text.strip()
            explanation_text = explanation_text.strip()

            if question_text and answer_text and explanation_text:
                questions.append(
                    QuestionResponse(
                        question=question_text,
                        answer=answer_text,
                        explanation=explanation_text,
                    )
                )

        return questions

    def create_quiz(self, quiz: QuizCreate) -> QuizResponse:
        """Create quiz from PDF file"""
        try:
            # Load PDF
            docs = self._load_pdf(quiz.path)

            # Build vectorstore
            vectorstore = self._build_vectorstore(docs)

            # Generate quiz
            quiz_text = self._generate_quiz(vectorstore)

            # Parse quiz into structured format
            questions = self._parse_quiz_response(quiz_text)

            # If parsing failed, create a fallback response
            if not questions:
                questions = [
                    QuestionResponse(
                        question="퀴즈 생성 중 파싱 오류가 발생했습니다. 다시 시도해주세요.",
                        answer="N/A",
                        explanation="시스템 오류로 인해 퀴즈를 정상적으로 파싱할 수 없었습니다.",
                    )
                ]

            return QuizResponse(data=questions)

        except FileNotFoundError as e:
            raise ValueError(f"PDF 파일을 찾을 수 없습니다: {str(e)}")
        except Exception as e:
            raise ValueError(f"퀴즈 생성 중 오류가 발생했습니다: {str(e)}")
