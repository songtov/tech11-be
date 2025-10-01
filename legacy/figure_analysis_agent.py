#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Figure Analysis Agent - 논문의 Figure들을 추출하고 분석하는 시스템
PDF에서 Figure를 추출하여 이미지 분석 및 관련 이론 설명을 생성합니다.
"""

import os
import re
import tempfile
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging

# 환경변수 로드
from dotenv import load_dotenv

load_dotenv()

# 필요한 라이브러리 임포트
import fitz  # PyMuPDF
from PIL import Image
import io
import base64

# LangChain 관련
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import AzureOpenAIEmbeddings, AzureChatOpenAI

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class FigureAnalysisAgent:
    """논문의 Figure들을 분석하는 에이전트"""

    def __init__(self, output_dir: str = "figure_analysis_results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # LLM 및 임베딩 설정
        self.llm_vision = self.get_llm(temperature=0.3, use_mini=False)
        self.llm_text = self.get_llm(temperature=0.2, use_mini=True)
        self.embeddings = self.get_embeddings()

        # Figure 정보를 저장할 리스트
        self.figures = []

    def get_llm(self, temperature: float = 0.2, use_mini: bool = True):
        """LLM 인스턴스 생성"""
        return AzureChatOpenAI(
            openai_api_version="2024-02-01",
            azure_deployment=(
                os.getenv("AOAI_DEPLOY_GPT4O_MINI")
                if use_mini
                else os.getenv("AOAI_DEPLOY_GPT4O")
            ),
            temperature=temperature,
            api_key=os.getenv("AOAI_API_KEY"),
            azure_endpoint=os.getenv("AOAI_ENDPOINT"),
        )

    def get_embeddings(self):
        """임베딩 모델 인스턴스 생성"""
        return AzureOpenAIEmbeddings(
            model=os.getenv("AOAI_DEPLOY_EMBED_3_LARGE"),
            openai_api_version="2024-02-01",
            api_key=os.getenv("AOAI_API_KEY"),
            azure_endpoint=os.getenv("AOAI_ENDPOINT"),
        )

    def load_pdf(self, pdf_path: str) -> fitz.Document:
        """PDF 파일을 로드합니다."""
        try:
            if pdf_path.startswith("http://") or pdf_path.startswith("https://"):
                # URL에서 PDF 다운로드
                response = requests.get(pdf_path, timeout=30)
                response.raise_for_status()
                pdf_doc = fitz.open(stream=response.content, filetype="pdf")
            else:
                # 로컬 파일 로드
                pdf_doc = fitz.open(pdf_path)

            logger.info(f"PDF 로드 완료: {len(pdf_doc)} 페이지")
            return pdf_doc
        except Exception as e:
            logger.error(f"PDF 로드 실패: {e}")
            raise

    def extract_figures_from_pdf(self, pdf_doc: fitz.Document) -> List[Dict]:
        """PDF에서 Figure들을 추출합니다."""
        figures = []

        # 전체 PDF 텍스트를 먼저 추출 (주변 컨텍스트 분석용)
        full_text = ""
        for page_num in range(len(pdf_doc)):
            full_text += pdf_doc[page_num].get_text() + "\n"

        for page_num in range(len(pdf_doc)):
            page = pdf_doc[page_num]

            # 텍스트에서 Figure 참조 찾기
            text = page.get_text()
            figure_matches = re.finditer(
                r"Figure\s+(\d+)[\s\S]*?(?=Figure\s+\d+|$)", text, re.IGNORECASE
            )

            for match in figure_matches:
                figure_text = match.group(0)
                figure_number = match.group(1)

                # Figure 캡션 추출
                caption_match = re.search(
                    r"Figure\s+\d+[:\s]*(.+?)(?:\n|$)", figure_text, re.IGNORECASE
                )
                caption = caption_match.group(1).strip() if caption_match else ""

                # Figure 주변 논문 내용 발췌 (Figure 앞뒤 1000자씩)
                figure_context = self.extract_figure_context(
                    full_text, figure_number, page_num + 1
                )

                # 이미지 영역 찾기
                image_list = page.get_images()
                if image_list:
                    try:
                        # 첫 번째 이미지를 Figure로 가정
                        img_index = 0
                        xref = image_list[img_index][0]
                        pix = fitz.Pixmap(pdf_doc, xref)

                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            # 이미지를 PIL Image로 변환
                            img_data = pix.tobytes("png")
                            img = Image.open(io.BytesIO(img_data))

                            # Figure 정보 저장
                            figure_info = {
                                "number": int(figure_number),
                                "page": page_num + 1,
                                "caption": caption,
                                "image": img,
                                "text_context": figure_text,
                                "surrounding_context": figure_context,
                            }
                            figures.append(figure_info)
                            logger.info(
                                f"Figure {figure_number} 추출 완료 (페이지 {page_num + 1})"
                            )

                        pix = None
                    except Exception as e:
                        logger.warning(f"Figure {figure_number} 이미지 추출 실패: {e}")
                        # 이미지 없이도 텍스트 정보만으로 Figure 정보 저장
                        figure_info = {
                            "number": int(figure_number),
                            "page": page_num + 1,
                            "caption": caption,
                            "image": None,
                            "text_context": figure_text,
                            "surrounding_context": figure_context,
                        }
                        figures.append(figure_info)
                        logger.info(
                            f"Figure {figure_number} 텍스트 정보만 추출 완료 (페이지 {page_num + 1})"
                        )

        logger.info(f"총 {len(figures)}개의 Figure 추출 완료")
        return figures

    def extract_figure_context(
        self, full_text: str, figure_number: str, page_num: int
    ) -> str:
        """Figure 주변의 논문 내용을 발췌합니다."""
        try:
            # Figure가 언급되는 모든 위치 찾기
            figure_mentions = []
            for match in re.finditer(
                rf"Figure\s+{figure_number}\b", full_text, re.IGNORECASE
            ):
                start_pos = match.start()
                figure_mentions.append(start_pos)

            if not figure_mentions:
                return ""

            # 가장 가까운 Figure 언급 위치 찾기
            target_page_start = full_text.find(f"Page {page_num}")
            if target_page_start == -1:
                target_page_start = 0

            closest_mention = min(
                figure_mentions, key=lambda x: abs(x - target_page_start)
            )

            # Figure 주변 1500자씩 발췌
            context_start = max(0, closest_mention - 1500)
            context_end = min(len(full_text), closest_mention + 1500)

            context = full_text[context_start:context_end]

            # 문장 단위로 정리
            sentences = re.split(r"[.!?]+", context)
            relevant_sentences = []

            for sentence in sentences:
                if any(
                    keyword in sentence.lower()
                    for keyword in [
                        "figure",
                        "model",
                        "method",
                        "result",
                        "analysis",
                        "experiment",
                    ]
                ):
                    relevant_sentences.append(sentence.strip())

            return " ".join(relevant_sentences[:10])  # 최대 10문장

        except Exception as e:
            logger.warning(f"Figure {figure_number} 주변 컨텍스트 추출 실패: {e}")
            return ""

    def analyze_figure_with_vision(self, figure_info: Dict) -> Dict:
        """Vision API를 사용하여 Figure를 분석합니다."""
        try:
            # 이미지가 있는 경우와 없는 경우를 구분하여 처리
            if figure_info["image"] is not None:
                # 이미지를 base64로 인코딩
                img_buffer = io.BytesIO()
                figure_info["image"].save(img_buffer, format="PNG")
                img_base64 = base64.b64encode(img_buffer.getvalue()).decode()

                # Vision API 호출을 위한 프롬프트
                vision_prompt = f"""
                이 논문의 Figure {figure_info['number']}를 분석해주세요.
                
                Figure 캡션: {figure_info['caption']}
                
                다음 항목들을 포함하여 분석해주세요:
                1. 이미지에 나타난 주요 요소들과 구조
                2. 차트, 그래프, 다이어그램의 유형과 내용
                3. 색상, 레이블, 축 등의 시각적 요소
                4. 데이터나 결과의 패턴과 특징
                5. 기술적 개념이나 방법론의 시각적 표현
                
                분석 결과를 한국어로 상세히 설명해주세요.
                """

                # Vision API 호출 (실제 구현에서는 Azure OpenAI Vision API 사용)
                # 여기서는 텍스트 기반 분석으로 대체
                analysis_result = self.analyze_figure_text_based(figure_info)
            else:
                # 이미지가 없는 경우 텍스트 기반 분석만 수행
                analysis_result = self.analyze_figure_text_based(figure_info)

            return {
                "figure_number": figure_info["number"],
                "visual_analysis": analysis_result,
                "caption": figure_info["caption"],
                "page": figure_info["page"],
            }

        except Exception as e:
            logger.error(f"Figure {figure_info['number']} 분석 실패: {e}")
            return {
                "figure_number": figure_info["number"],
                "visual_analysis": f"분석 중 오류 발생: {e}",
                "caption": figure_info["caption"],
                "page": figure_info["page"],
            }

    def analyze_figure_text_based(self, figure_info: Dict) -> str:
        """텍스트 기반으로 Figure를 분석합니다."""
        try:
            # Figure 관련 텍스트 컨텍스트 분석
            context_prompt = f"""
            논문의 Figure {figure_info['number']}를 분석해주세요.
            
            Figure 캡션: {figure_info['caption']}
            Figure 관련 텍스트: {figure_info['text_context']}
            Figure 주변 논문 내용: {figure_info['surrounding_context']}
            
            다음 내용을 확정적으로 설명해주세요 (추측이나 불확실한 표현 사용하지 말 것):
            
            1. Figure의 구체적인 내용과 구조
            2. 나타난 데이터나 결과의 명확한 의미
            3. 사용된 방법론이나 기술의 정확한 설명
            4. 논문에서 이 Figure가 증명하는 핵심 주장
            
            한국어로 간결하고 명확하게 설명해주세요.
            """

            prompt_template = PromptTemplate.from_template(context_prompt)
            analysis_chain = prompt_template | self.llm_text | StrOutputParser()
            analysis = analysis_chain.invoke({})

            return analysis

        except Exception as e:
            logger.error(f"텍스트 기반 Figure 분석 실패: {e}")
            return f"분석 중 오류가 발생했습니다: {e}"

    def generate_theory_explanation(self, figure_analysis: Dict, pdf_text: str) -> str:
        """Figure와 관련된 이론적 설명을 생성합니다."""
        try:
            theory_prompt = f"""
            논문의 Figure {figure_analysis['figure_number']}와 관련된 이론적 설명을 작성해주세요.
            
            Figure 분석 결과: {figure_analysis['visual_analysis']}
            Figure 캡션: {figure_analysis['caption']}
            논문 관련 내용: {pdf_text[:2000]}...
            
            위의 내용들을 바탕으로 Figure {figure_analysis['figure_number']}에 대한 이론적 설명을 논리적이고 명확하게 하나의 통합된 설명으로 작성해주세요.
            
            핵심 이론, 방법론, 결과의 의미, 실무 적용 등을 자연스럽게 연결하여 하나의 완성된 설명으로 만들어주세요.
            불확실한 표현은 사용하지 말고 확정적으로 설명해주세요.
            """

            prompt_template = PromptTemplate.from_template(theory_prompt)
            theory_chain = prompt_template | self.llm_text | StrOutputParser()
            theory_explanation = theory_chain.invoke({})

            return theory_explanation

        except Exception as e:
            logger.error(f"이론 설명 생성 실패: {e}")
            return f"이론 설명 생성 중 오류가 발생했습니다: {e}"

    def save_figure_analysis(self, figure_analyses: List[Dict], pdf_filename: str):
        """Figure 분석 결과를 파일로 저장합니다."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = Path(pdf_filename).stem

        # 전체 파일 하나만 생성
        filename = f"{base_filename}_Figures_{timestamp}.txt"
        filepath = self.output_dir / filename

        content = ""

        for analysis in figure_analyses:
            content += f"Figure {analysis['figure_number']}: {analysis['caption']}\n\n{analysis['theory_explanation']}\n\n"

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        logger.info(f"Figure 분석 결과 저장: {filepath}")
        return filepath

    def process_pdf_figures(self, pdf_path: str) -> List[Dict]:
        """PDF의 모든 Figure를 분석합니다."""
        logger.info(f"PDF Figure 분석 시작: {pdf_path}")

        try:
            # PDF 로드
            pdf_doc = self.load_pdf(pdf_path)

            # Figure 추출
            figures = self.extract_figures_from_pdf(pdf_doc)

            if not figures:
                logger.warning("추출된 Figure가 없습니다.")
                return []

            # PDF 텍스트 추출 (이론 설명용)
            pdf_text = ""
            for page in pdf_doc:
                pdf_text += page.get_text() + "\n"

            # 각 Figure 분석
            figure_analyses = []
            for figure in figures:
                logger.info(f"Figure {figure['number']} 분석 중...")

                # 시각적 분석
                visual_analysis = self.analyze_figure_with_vision(figure)

                # 이론적 설명 생성
                theory_explanation = self.generate_theory_explanation(
                    visual_analysis, pdf_text
                )

                # 결과 통합
                analysis_result = {
                    "figure_number": figure["number"],
                    "page": figure["page"],
                    "caption": figure["caption"],
                    "visual_analysis": visual_analysis["visual_analysis"],
                    "theory_explanation": theory_explanation,
                }

                figure_analyses.append(analysis_result)
                logger.info(f"Figure {figure['number']} 분석 완료")

            # 결과 저장
            summary_file = self.save_figure_analysis(figure_analyses, pdf_path)

            logger.info(f"모든 Figure 분석 완료. 결과 저장: {summary_file}")
            return figure_analyses

        except Exception as e:
            logger.error(f"PDF Figure 분석 실패: {e}")
            raise
        finally:
            if "pdf_doc" in locals():
                pdf_doc.close()


def main():
    """메인 실행 함수"""
    print("🔍 Figure Analysis Agent - 논문 Figure 분석 시스템")
    print("=" * 60)

    # 다운로드된 논문들 확인
    papers_dir = Path("downloaded_papers")
    if not papers_dir.exists():
        print("❌ downloaded_papers 디렉토리가 없습니다.")
        return

    pdf_files = list(papers_dir.glob("*.pdf"))
    if not pdf_files:
        print("❌ 분석할 PDF 파일이 없습니다.")
        return

    print(f"\n📚 발견된 PDF 파일들:")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"   {i}. {pdf_file.name}")

    try:
        # PDF 선택
        while True:
            try:
                choice = input(
                    f"\n분석할 PDF를 선택하세요 (1-{len(pdf_files)}): "
                ).strip()
                pdf_index = int(choice) - 1

                if 0 <= pdf_index < len(pdf_files):
                    selected_pdf = pdf_files[pdf_index]
                    break
                else:
                    print("❌ 잘못된 번호입니다. 다시 입력해주세요.")
            except ValueError:
                print("❌ 숫자를 입력해주세요.")

        # Figure 분석 실행
        agent = FigureAnalysisAgent()
        print(f"\n🔍 '{selected_pdf.name}'의 Figure들을 분석합니다...")

        results = agent.process_pdf_figures(str(selected_pdf))

        if results:
            print(f"\n✅ 분석 완료! {len(results)}개의 Figure가 분석되었습니다.")
            print(f"📁 결과 파일들이 'figure_analysis_results' 폴더에 저장되었습니다.")
        else:
            print("\n❌ 분석할 Figure를 찾을 수 없습니다.")

    except KeyboardInterrupt:
        print("\n프로그램을 종료합니다.")
    except Exception as e:
        logger.error(f"프로그램 실행 중 오류: {e}")
        print(f"❌ 오류가 발생했습니다: {e}")


if __name__ == "__main__":
    main()
