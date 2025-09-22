#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Boot Camp Lab - Main Agent Controller
논문 검색 → PDF 다운로드 → 퀴즈 생성 및 TTS 팟캐스트 제작을 자동화
"""

import os
import sys
import subprocess
import time
from pathlib import Path
from typing import List, Optional

# 기존 에이전트들 임포트
from axpress_scholar_agent_ver1 import AXPressScholarAgent, Paper
from quiz_tts_agent import PDFQuizSystem

class MainAgentController:
    """논문 검색부터 퀴즈 생성까지 통합 관리하는 메인 컨트롤러"""
    
    def __init__(self):
        self.scholar_agent = AXPressScholarAgent()
        self.quiz_system = PDFQuizSystem()
        self.downloaded_papers_dir = Path("downloaded_papers")
        
    def find_downloaded_papers(self) -> List[str]:
        """downloaded_papers 폴더에서 PDF 파일들을 찾습니다."""
        if not self.downloaded_papers_dir.exists():
            return []
        
        pdf_files = list(self.downloaded_papers_dir.glob("*.pdf"))
        return [str(f) for f in pdf_files]
    
    def get_latest_pdf(self) -> Optional[str]:
        """가장 최근에 다운로드된 PDF 파일을 반환합니다."""
        pdf_files = self.find_downloaded_papers()
        if not pdf_files:
            return None
        
        # 파일 수정 시간 기준으로 정렬하여 가장 최근 파일 반환
        latest_file = max(pdf_files, key=lambda f: os.path.getmtime(f))
        return latest_file
    
    def run_scholar_agent(self) -> bool:
        """AXPress Scholar Agent를 실행하여 논문을 다운로드합니다."""
        print("\n🔬 1단계: AXPress Scholar Agent 실행")
        print("=" * 60)
        
        try:
            # 지원 도메인 표시
            domains = ["제조", "금융", "CLOUD", "통신", "유통/물류", "Gen AI"]
            print("\n📋 지원 도메인:")
            for i, domain in enumerate(domains, 1):
                print(f"   {i}. {domain}")
            
            # 도메인 선택
            while True:
                try:
                    choice = input(f"\n도메인을 선택하세요 (1-{len(domains)}): ").strip()
                    domain_index = int(choice) - 1
                    
                    if 0 <= domain_index < len(domains):
                        selected_domain = domains[domain_index]
                        break
                    else:
                        print("❌ 잘못된 번호입니다. 다시 입력해주세요.")
                except ValueError:
                    print("❌ 숫자를 입력해주세요.")
            
            print(f"\n🔍 '{selected_domain}' 도메인에서 논문을 검색합니다...")
            
            # 논문 검색
            papers = self.scholar_agent.fetch_papers(selected_domain)
            
            if not papers:
                print("❌ 검색된 논문이 없습니다.")
                return False
            
            # 결과 표시
            self.scholar_agent.display_papers(papers)
            
            # PDF 다운로드 선택
            print(f"\n📄 총 {len(papers)}편의 논문 중에서 PDF를 다운로드할 논문을 선택하세요.")
            print("번호를 입력하세요 (0: 종료): ", end="")
            
            try:
                choice = int(input().strip())
                if choice == 0:
                    print("프로그램을 종료합니다.")
                    return False
                elif 1 <= choice <= len(papers):
                    selected_paper = papers[choice - 1]
                    print(f"\n선택된 논문: {selected_paper.title}")
                    
                    filepath = self.scholar_agent.download_pdf(selected_paper)
                    
                    if filepath:
                        print(f"\n✅ PDF 다운로드가 완료되었습니다!")
                        print(f"저장 위치: {filepath}")
                        return True
                    else:
                        print("\n❌ PDF 다운로드에 실패했습니다.")
                        return False
                else:
                    print("❌ 잘못된 번호입니다.")
                    return False
            except ValueError:
                print("❌ 숫자를 입력해주세요.")
                return False
                
        except KeyboardInterrupt:
            print("\n프로그램을 종료합니다.")
            return False
        except Exception as e:
            print(f"❌ 오류가 발생했습니다: {e}")
            return False
    
    def run_quiz_agent(self, pdf_path: str) -> bool:
        """Quiz TTS Agent를 실행하여 PDF를 분석하고 퀴즈를 생성합니다."""
        print(f"\n🎓 2단계: Quiz TTS Agent 실행")
        print("=" * 60)
        print(f"📄 분석할 PDF: {os.path.basename(pdf_path)}")
        
        try:
            # PDFQuizSystem으로 PDF 처리
            success = self.quiz_system.process_pdf(pdf_path)
            
            if success:
                print("\n✅ Quiz TTS Agent 실행 완료!")
                return True
            else:
                print("\n❌ Quiz TTS Agent 실행 실패!")
                return False
                
        except Exception as e:
            print(f"❌ Quiz TTS Agent 실행 중 오류: {e}")
            return False
    
    def run_automatic_workflow(self) -> bool:
        """논문 검색부터 퀴즈 생성까지 자동으로 실행합니다."""
        print("\n🚀 자동 워크플로우 시작")
        print("=" * 60)
        
        # 1단계: 논문 검색 및 다운로드
        if not self.run_scholar_agent():
            return False
        
        # 잠시 대기
        print("\n⏳ 잠시 대기 중...")
        time.sleep(2)
        
        # 2단계: 가장 최근 다운로드된 PDF로 퀴즈 생성
        latest_pdf = self.get_latest_pdf()
        if not latest_pdf:
            print("❌ 다운로드된 PDF 파일을 찾을 수 없습니다.")
            return False
        
        print(f"\n📄 최근 다운로드된 PDF를 자동 선택: {os.path.basename(latest_pdf)}")
        
        if not self.run_quiz_agent(latest_pdf):
            return False
        
        print("\n🎉 전체 워크플로우 완료!")
        return True
    
    def run_manual_workflow(self) -> bool:
        """수동으로 각 단계를 선택하여 실행합니다."""
        while True:
            print("\n" + "="*80)
            print("🤖 AI Boot Camp Lab - Main Agent Controller")
            print("="*80)
            print("\n사용 가능한 작업:")
            print("1. 논문 검색 및 PDF 다운로드 (AXPress Scholar Agent)")
            print("2. PDF 분석 및 퀴즈 생성 (Quiz TTS Agent)")
            print("3. 자동 워크플로우 (1번 + 2번 연속 실행)")
            print("4. 종료")
            print("="*80)
            
            try:
                choice = input("\n작업을 선택하세요 (1-4): ").strip()
                
                if choice == "1":
                    self.run_scholar_agent()
                elif choice == "2":
                    # 다운로드된 PDF 파일 목록 표시
                    pdf_files = self.find_downloaded_papers()
                    if not pdf_files:
                        print("❌ downloaded_papers 폴더에 PDF 파일이 없습니다.")
                        print("   먼저 1번 작업으로 논문을 다운로드해주세요.")
                        continue
                    
                    print(f"\n📁 다운로드된 PDF 파일 ({len(pdf_files)}개):")
                    for i, pdf_file in enumerate(pdf_files, 1):
                        filename = os.path.basename(pdf_file)
                        print(f"   {i}. {filename}")
                    
                    if len(pdf_files) == 1:
                        selected_pdf = pdf_files[0]
                        print(f"\n📄 자동 선택: {os.path.basename(selected_pdf)}")
                    else:
                        while True:
                            try:
                                pdf_choice = input(f"\n분석할 PDF 파일을 선택하세요 (1-{len(pdf_files)}): ").strip()
                                pdf_choice_idx = int(pdf_choice) - 1
                                
                                if 0 <= pdf_choice_idx < len(pdf_files):
                                    selected_pdf = pdf_files[pdf_choice_idx]
                                    break
                                else:
                                    print("❌ 잘못된 번호입니다. 다시 입력해주세요.")
                            except ValueError:
                                print("❌ 숫자를 입력해주세요.")
                    
                    self.run_quiz_agent(selected_pdf)
                    
                elif choice == "3":
                    self.run_automatic_workflow()
                elif choice == "4":
                    print("\n👋 프로그램을 종료합니다.")
                    break
                else:
                    print("❌ 잘못된 선택입니다. 1-4 중에서 선택해주세요.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 프로그램을 종료합니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류가 발생했습니다: {e}")
                input("계속하려면 Enter를 누르세요...")

def main():
    """메인 함수"""
    print("🤖 AI Boot Camp Lab - Main Agent Controller")
    print("논문 검색 → PDF 다운로드 → 퀴즈 생성 및 TTS 팟캐스트 제작")
    print("=" * 80)
    
    try:
        controller = MainAgentController()
        
        # 실행 모드 선택
        print("\n실행 모드를 선택하세요:")
        print("1. 자동 워크플로우 (논문 검색 → PDF 다운로드 → 퀴즈 생성)")
        print("2. 수동 모드 (각 단계별 선택)")
        
        while True:
            try:
                mode_choice = input("\n모드를 선택하세요 (1-2): ").strip()
                
                if mode_choice == "1":
                    controller.run_automatic_workflow()
                    break
                elif mode_choice == "2":
                    controller.run_manual_workflow()
                    break
                else:
                    print("❌ 1 또는 2를 입력해주세요.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 프로그램을 종료합니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류가 발생했습니다: {e}")
                
    except KeyboardInterrupt:
        print("\n\n👋 프로그램을 종료합니다.")
    except Exception as e:
        print(f"\n❌ 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()
