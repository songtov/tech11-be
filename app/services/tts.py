from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from gtts import gTTS

# ===========================================================
# ✅ DB 제거 버전 - 파일 시스템 기반 단일 서비스
# ===========================================================


def clean_text(text: str) -> str:
    """TTS용 텍스트 정제"""
    cleaned = re.sub(r"[#*>•\-]+", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


class TTSService:
    def __init__(self):
        self.output_dir = Path("output/tts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.legacy_papers_dir = Path("legacy/downloaded_papers")

    # =====================================================
    # 1️⃣ 멀티에이전트 실행 (임시 더미 구현 or 실제 호출)
    # =====================================================
    async def _run_legacy_multi_agent(self, pdf_path: str) -> Dict[str, Any]:
        """
        Legacy multitest.py의 run_multi_agent 함수를 직접 호출
        PDF → 벡터스토어 → summary/quiz/explainer 생성
        """
        try:
            import sys

            legacy_path = Path(__file__).parent.parent.parent / "legacy"
            sys.path.insert(0, str(legacy_path))

            from multitest import run_multi_agent  # type: ignore

            print("🎯 Legacy 멀티에이전트 실행 시작: {pdf_path}")
            final_state = run_multi_agent(pdf_path)
            print("✅ Legacy 멀티에이전트 실행 완료")

            return {
                "summary": final_state.get("summary", ""),
                "explainer": final_state.get("explainer", ""),
                "quiz": final_state.get("quiz", ""),
            }
        except Exception as e:
            print("❌ Legacy 멀티에이전트 실행 실패: {e}")
            raise e

    # =====================================================
    # 2️⃣ PDF → 멀티에이전트 → TTS 변환 전체 흐름
    # =====================================================
    async def process_pdf_to_tts(self, pdf_path: str) -> Dict[str, Any]:
        """
        Legacy multitest.py의 node_tts 로직을 정확히 따름
        PDF → 멀티에이전트 → explainer만 TTS 변환
        """
        try:
            # 1. 멀티에이전트 실행 (legacy run_multi_agent 호출)
            print(f"📘 Processing PDF: {pdf_path}")
            agent_result = await self._run_legacy_multi_agent(pdf_path)

            # 2. Legacy node_tts와 동일: explainer만 사용
            script = agent_result.get("explainer", "")
            if not script:
                # Legacy와 동일: explainer가 없으면 빈 결과 반환
                return {
                    "summary": agent_result.get("summary", ""),
                    "explainer": "",
                    "tts_id": None,
                    "audio_filename": None,
                    "audio_file_path": None,
                }

            # 3. Legacy node_tts와 동일: clean_text 적용
            script_clean = clean_text(script)

            # 4. Legacy node_tts와 동일: 파일명 생성
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"industry_explainer_{ts}.mp3"
            file_path = self.output_dir / audio_filename

            # 5. Legacy node_tts와 동일: gTTS 생성 및 저장
            tts = gTTS(text=script_clean, lang="ko")
            tts.save(str(file_path))
            print(f"🎧 TTS 저장 완료: {audio_filename}")

            return {
                "summary": agent_result.get("summary", ""),
                "explainer": script,
                "tts_id": ts,
                "audio_filename": audio_filename,
                "audio_file_path": str(file_path),
            }

        except Exception as e:
            print("❌ PDF → TTS 처리 실패: {e}")
            raise e

    # =====================================================
    # 3️⃣ 파일 기반 헬퍼 함수들
    # =====================================================
    def get_audio_file_by_filename(self, filename: str) -> str | None:
        """생성된 오디오 파일 경로 반환"""
        file_path = self.output_dir / filename
        return str(file_path) if file_path.exists() else None

    def get_first_legacy_pdf(self) -> str | None:
        """legacy/downloaded_papers 폴더의 첫 번째 PDF 반환"""
        pdf_files = list(self.legacy_papers_dir.glob("*.pdf"))
        return str(pdf_files[0]) if pdf_files else None
