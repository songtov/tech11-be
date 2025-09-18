# MyHR & AX College — 최신 정보 학습 및 이력 관리를 지원하는 웹 서비스

## 주요 기능 (v1)
- MyHR & AX College 테마를 참고한 클론 코딩을 통해 유사한 UI 구현
- 상세 페이지 및 랜딩 구조는 현재 구상 단계 (추후 구체화 예정)

## 실행 환경
- Node.js 18+
- 의존성 설치: `npm i`
- 실행: `npm run dev`  
  - MyHR → `http://localhost:3000`  
  - AX College → `http://localhost:3001`
- Next.js 기반 빌드 (React 18 + TypeScript)
- 환경 변수: `.env` (추후 필요 시 활용 예정)

---

## 기술 스택
- **프레임워크**: React 18, TypeScript
- **라우팅**: React Router v6.27+
- **상태 관리**  
  - 서버 상태: React Query  
  - 클라이언트 상태: Zustand
- **HTTP 통신**: Axios(+인터셉터)
- **폼/검증**: React Hook Form + Zod
- **UI/유틸리티**: classnames, date-fns, react-hot-toast(또는 sonner), lucide-react
- **테스트**: Vitest + React Testing Library + Playwright (e2e)
- **품질 관리**: ESLint(+typescript-eslint, react-hooks), Prettier, Husky(+lint-staged)
- **국제화(i18n)**: i18next (키 분리만 적용)
