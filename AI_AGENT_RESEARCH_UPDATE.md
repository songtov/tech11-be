# AI Agent 기반 논문 검색 시스템 업데이트

## 🎯 개요

Research paper 검색 기능을 AI Agent 방식으로 변경했습니다. 기존의 저널 기반 검색에서 AI 모델에게 프롬프트를 보내서 논문을 추천받고, 그 결과를 바탕으로 arXiv에서 실제 논문을 검색하는 방식으로 개선되었습니다.

## 🔄 변경된 워크플로우

### 기존 방식
```
도메인 선택 → 저널 기반 검색 → Semantic Scholar API → arXiv 검색 → 결과 반환
```

### 새로운 AI Agent 방식
```
도메인 선택 → AI 프롬프트 생성 → Azure OpenAI 호출 → AI 추천 파싱 → arXiv 검색 → 결과 반환
```

## 🚀 주요 변경사항

### 1. **AI 모델 통신 추가**
- Azure OpenAI GPT-4o-mini 모델 사용
- TTS 서비스와 동일한 AI 모델 활용
- 프롬프트 기반 논문 추천 시스템

### 2. **도메인별 맞춤 프롬프트**
각 도메인에 맞는 선도 기관 정보를 포함한 프롬프트:

- **AI**: OpenAI, Samsung, DeepSeek, Google, Microsoft, Anthropic + NeurIPS, ICML, ICLR, AAAI
- **금융**: Goldman Sachs, JP Morgan, BlackRock, Citadel, Two Sigma + AFA, WFA, NBER
- **통신**: Qualcomm, Ericsson, Nokia, Huawei, Samsung + IEEE Communications, ACM SIGCOMM
- **제조**: Tesla, Toyota, BMW, Siemens, General Electric + IEEE Robotics, CIRP Annals
- **유통/물류**: Amazon, FedEx, UPS, DHL, Alibaba + Transportation Research, Supply Chain Management
- **클라우드**: AWS, Microsoft Azure, Google Cloud, IBM Cloud, Oracle Cloud + IEEE Cloud Computing, ACM Computing Surveys

### 3. **AI 프롬프트 예시**
```
***AI 도메인에 대해 공부하고자해. 학습자료로는 논문을 사용할 것이야. 
너는 나에게 논문을 추천해주는 에이전트야. 추천 기준으로는 'AI 도메인에서 업계를 선도하고있는 기업, 또는 연구소급에서 개제한 논문을 찾아줘'. 

AI의 경우에는 openai, samsung, deepseek, google, microsoft, anthropic 등과 같은 기관 및 neurips, icml, iclr, aaai 등의 저명한 학회에 올라온 최신 논문을 골라주면 되는 것이지.

단, 반드시 https://arxiv.org/에 있는 논문을 5편 추천해줘. 
글고 논문의 제목, 저자, 년도만 정보를 추출해줘.

응답 형식:
제목: [논문 제목]
저자: [저자명들]
년도: [발행년도]
arXiv ID: [arXiv ID]

이런 형식으로 5개 논문을 추천해줘.
```

### 4. **다단계 Fallback 시스템**
1. **AI 추천**: AI 모델이 도메인별 선도 기관 논문 추천
2. **arXiv 검색**: 추천된 논문을 arXiv에서 실제 검색
3. **보완 검색**: 부족한 경우 기존 arXiv 키워드 검색
4. **최종 Fallback**: 알려진 arXiv ID + 더미 논문

## 📁 수정된 파일들

### `app/services/research.py`
- `SimplifiedScholarAgent` 클래스에 AI 모델 통신 기능 추가
- `fetch_papers` 메서드를 AI Agent 방식으로 완전 재작성
- 새로운 메서드들 추가:
  - `_get_ai_recommendations()`: AI 모델과 통신
  - `_parse_ai_recommendations()`: AI 응답 파싱
  - `_search_arxiv_by_recommendations()`: AI 추천 기반 arXiv 검색
  - `_fetch_paper_by_arxiv_id()`: 특정 arXiv ID로 논문 검색
  - `_fallback_search()`: 기존 방식으로 Fallback

### 기존 기능 유지
- **API 엔드포인트**: `/research/search`, `/research/download/{id}`, `/research/serve/{id}` 모두 동일
- **데이터베이스 캐싱**: 하루 단위 캐싱 시스템 유지
- **S3 저장**: PDF 다운로드 및 S3 저장 기능 유지
- **에러 처리**: 기존 에러 처리 로직 유지

## 🧪 테스트

### 테스트 스크립트
```bash
python test_ai_agent_research.py
```

### API 테스트
```bash
# AI 도메인 논문 검색
curl -X POST "http://127.0.0.1:8000/research/search" \
     -H "Content-Type: application/json" \
     -d '{"domain": "AI"}'

# 금융 도메인 논문 검색
curl -X POST "http://127.0.0.1:8000/research/search" \
     -H "Content-Type: application/json" \
     -d '{"domain": "FINANCE"}'
```

## 🔧 환경 설정

### 필수 환경 변수
```env
# Azure OpenAI 설정 (TTS와 동일)
AOAI_API_KEY=your_azure_openai_api_key
AOAI_ENDPOINT=https://your-resource.openai.azure.com/
AOAI_DEPLOY_GPT4O_MINI=your-gpt-4o-mini-deployment

# S3 설정 (기존과 동일)
S3_BUCKET=your-s3-bucket
AWS_ACCESS_KEY=your-aws-access-key
AWS_SECRET_KEY=your-aws-secret-key
```

## 🎯 장점

1. **도메인별 맞춤화**: 각 도메인의 선도 기관 정보를 활용한 정확한 추천
2. **최신 논문**: AI가 최신 트렌드를 반영한 논문 추천
3. **유연성**: 프롬프트 수정으로 쉽게 검색 기준 변경 가능
4. **안정성**: 다단계 Fallback으로 검색 실패 시에도 안정적 동작
5. **기존 호환성**: API 인터페이스와 데이터 형식 모두 동일하게 유지

## 🔮 향후 개선 방향

1. **프롬프트 최적화**: 도메인별 프롬프트를 더 정교하게 튜닝
2. **캐싱 개선**: AI 추천 결과도 캐싱하여 성능 향상
3. **추천 품질 평가**: AI 추천 결과의 품질을 평가하는 메트릭 추가
4. **다양한 AI 모델**: 필요에 따라 다른 AI 모델도 활용 가능하도록 확장
