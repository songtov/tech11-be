# AI Boot Camp Lab - Main Agent Controller API 사용 가이드

## 개요
main.py 기반으로 구축된 FastAPI 서버입니다. 논문 검색부터 멀티에이전트 기반 퀴즈/요약/해설 생성 및 TTS 팟캐스트 제작까지 자동화하는 REST API를 제공합니다.

**서버 주소**: `http://127.0.0.1:8000/`

## 🚀 서버 실행

```bash
python fastapi_main.py
```

서버가 실행되면 다음 주소에서 API 문서를 확인할 수 있습니다:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## 📋 지원 도메인

- 제조 (manufacturing)
- 금융 (finance)
- CLOUD (cloud computing)
- 통신 (telecommunications)
- 유통/물류 (logistics)
- Gen AI (artificial intelligence)

## 🔗 API 엔드포인트

### 1. 기본 정보

#### GET `/`
- **설명**: API 기본 정보 반환
- **응답**: API 버전, 지원 도메인, 기능 목록

```bash
curl http://127.0.0.1:8000/
```

#### GET `/domains`
- **설명**: 지원되는 도메인 목록 반환
- **응답**: 도메인 배열과 개수

```bash
curl http://127.0.0.1:8000/domains
```

#### GET `/health`
- **설명**: 서버 상태 확인
- **응답**: 서버 상태, 타임스탬프, 버전 정보

```bash
curl http://127.0.0.1:8000/health
```

### 2. 논문 검색 및 다운로드

#### POST `/search/papers`
- **설명**: 도메인별 논문 검색 (Semantic Scholar + arXiv)
- **요청 본문**:
```json
{
  "domain": "Gen AI",
  "additional_keywords": "machine learning"
}
```
- **응답**: 논문 목록 (PaperResponse 배열)

```bash
curl -X POST "http://127.0.0.1:8000/search/papers" \
     -H "Content-Type: application/json" \
     -d '{"domain": "Gen AI"}'
```

#### POST `/download/pdf`
- **설명**: 논문 PDF 다운로드
- **요청 본문**:
```json
{
  "paper_index": 0,
  "papers_data": [
    {
      "id": "paper_id",
      "title": "논문 제목",
      "pdf_url": "https://arxiv.org/pdf/xxx.pdf",
      ...
    }
  ]
}
```
- **응답**: 다운로드 성공/실패 및 파일 경로

### 3. 멀티에이전트 처리

#### POST `/multiagent/process`
- **설명**: PDF 분석 및 요약/퀴즈/해설/TTS 생성
- **요청 본문**:
```json
{
  "pdf_path": "downloaded_papers/논문파일.pdf"
}
```
- **응답**: 생성된 요약, 퀴즈, 해설, 그림 분석, TTS 파일 정보

```bash
curl -X POST "http://127.0.0.1:8000/multiagent/process" \
     -H "Content-Type: application/json" \
     -d '{"pdf_path": "downloaded_papers/sample.pdf"}'
```

### 4. 전체 워크플로우

#### POST `/workflow/start`
- **설명**: 전체 워크플로우 시작 (논문 검색 → PDF 다운로드 → 멀티에이전트 처리)
- **요청 본문**:
```json
{
  "domain": "Gen AI",
  "additional_keywords": "deep learning",
  "paper_index": 0
}
```
- **응답**: 워크플로우 ID 및 시작 메시지

```bash
curl -X POST "http://127.0.0.1:8000/workflow/start" \
     -H "Content-Type: application/json" \
     -d '{"domain": "Gen AI", "paper_index": 0}'
```

#### GET `/workflow/status/{workflow_id}`
- **설명**: 워크플로우 상태 조회
- **응답**: 진행 상태, 현재 단계, 결과

```bash
curl http://127.0.0.1:8000/workflow/status/workflow_20250930_123456
```

#### GET `/workflow/list`
- **설명**: 실행 중인 워크플로우 목록
- **응답**: 워크플로우 ID 목록

```bash
curl http://127.0.0.1:8000/workflow/list
```

### 5. 유틸리티

#### GET `/papers/downloaded`
- **설명**: 다운로드된 PDF 파일 목록
- **응답**: 파일 정보 (이름, 경로, 크기, 수정일)

```bash
curl http://127.0.0.1:8000/papers/downloaded
```

## 📝 사용 예제

### 예제 1: 단계별 실행

```python
import requests

# 1. 논문 검색
search_response = requests.post("http://127.0.0.1:8000/search/papers", 
                               json={"domain": "Gen AI"})
papers = search_response.json()

# 2. PDF 다운로드
download_response = requests.post("http://127.0.0.1:8000/download/pdf",
                                 json={"paper_index": 0, "papers_data": papers})
download_result = download_response.json()

# 3. 멀티에이전트 처리
multiagent_response = requests.post("http://127.0.0.1:8000/multiagent/process",
                                   json={"pdf_path": download_result["filepath"]})
results = multiagent_response.json()
```

### 예제 2: 전체 워크플로우 실행

```python
import requests
import time

# 워크플로우 시작
workflow_response = requests.post("http://127.0.0.1:8000/workflow/start",
                                 json={"domain": "Gen AI", "paper_index": 0})
workflow_id = workflow_response.json()["workflow_id"]

# 상태 확인 (폴링)
while True:
    status_response = requests.get(f"http://127.0.0.1:8000/workflow/status/{workflow_id}")
    status = status_response.json()
    
    print(f"진행률: {status['progress']}% - {status['current_step']}")
    
    if status["status"] in ["completed", "failed"]:
        print("워크플로우 완료!")
        if status["status"] == "completed":
            print("결과:", status["results"])
        break
    
    time.sleep(5)  # 5초마다 상태 확인
```

## 🔧 환경 설정

### 필수 환경 변수 (.env 파일)

```env
AOAI_API_KEY=your_azure_openai_api_key
AOAI_ENDPOINT=https://your-resource.openai.azure.com/
AOAI_DEPLOY_GPT4O_MINI=your-gpt-4o-mini-deployment
AOAI_DEPLOY_GPT4O=your-gpt-4o-deployment
AOAI_DEPLOY_EMBED_3_LARGE=your-embedding-deployment
```

### 필수 라이브러리

```bash
pip install fastapi uvicorn
pip install langchain langchain-openai langchain-community
pip install langgraph
pip install gtts
pip install pymupdf
pip install faiss-cpu
pip install python-dotenv
pip install requests
```

## 📊 응답 형식

### PaperResponse
```json
{
  "id": "arxiv_id",
  "title": "논문 제목",
  "authors": ["저자1", "저자2"],
  "published_date": "2024-01-01T00:00:00Z",
  "updated_date": "2024-01-01T00:00:00Z",
  "abstract": "논문 요약",
  "categories": ["cs.AI"],
  "pdf_url": "https://arxiv.org/pdf/xxx.pdf",
  "arxiv_url": "https://arxiv.org/abs/xxx",
  "citation_count": 100,
  "relevance_score": 0.95
}
```

### MultiAgentResponse
```json
{
  "success": true,
  "message": "멀티에이전트 처리가 완료되었습니다.",
  "summary": "생성된 요약 텍스트",
  "quiz": "생성된 퀴즈 텍스트",
  "explainer": "생성된 해설 텍스트",
  "figure_analysis": "생성된 그림 분석 텍스트",
  "tts_file": "industry_explainer_20250930_123456.mp3"
}
```

## ⚠️ 주의사항

1. **API 키**: Azure OpenAI API 키가 올바르게 설정되어야 합니다.
2. **파일 경로**: PDF 파일 경로는 서버의 실제 파일 시스템 경로를 사용해야 합니다.
3. **타임아웃**: 멀티에이전트 처리는 시간이 오래 걸릴 수 있습니다.
4. **동시 실행**: 여러 워크플로우를 동시에 실행할 수 있지만, 리소스 사용량을 고려해야 합니다.

## 🐛 오류 처리

모든 API는 적절한 HTTP 상태 코드와 함께 오류 메시지를 반환합니다:

- `400 Bad Request`: 잘못된 요청
- `404 Not Found`: 리소스를 찾을 수 없음
- `500 Internal Server Error`: 서버 내부 오류

오류 응답 예시:
```json
{
  "detail": "지원하지 않는 도메인입니다. 지원 도메인: ['제조', '금융', 'CLOUD', '통신', '유통/물류', 'Gen AI']"
}
```
