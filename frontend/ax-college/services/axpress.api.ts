import { api } from "./api"
import type { ArticleCard, Article, Paper, CommunityPost } from "@/types/axpress"

// TypeScript interfaces for API parameters
export interface ArticlesParams {
  category?: string
  q?: string
  page?: number
  size?: number
}

export interface PapersParams {
  q?: string
  tags?: string[]
  from?: string
  to?: string
  page?: number
  size?: number
}

export interface CommunityParams {
  q?: string
  sort?: "recent" | "popular"
  page?: number
  size?: number
}

// Mock data exports - these are the exports that were missing
export const mockArticles: ArticleCard[] = [
  {
    id: "1",
    title: "AX College 새로운 교육과정 안내",
    summary: "2024년 새로운 교육과정이 출시되었습니다.",
    category: "news",
    tags: ["교육", "신규"],
    thumb: null,
    publishedAt: "2024-01-15",
    views: 1250,
  },
  {
    id: "2",
    title: "수강신청 일정 공지",
    summary: "2024년 1분기 수강신청 일정을 안내드립니다.",
    category: "notice",
    tags: ["수강신청", "일정"],
    thumb: null,
    publishedAt: "2024-01-10",
    views: 890,
  },
  {
    id: "3",
    title: "온라인 세미나 개최 안내",
    summary: "AI와 교육의 미래를 주제로 한 온라인 세미나가 개최됩니다.",
    category: "event",
    tags: ["세미나", "AI"],
    thumb: null,
    publishedAt: "2024-01-08",
    views: 567,
  },
]

export const mockPapers: Paper[] = [
  {
    id: "1",
    title: "AI-Driven Personalized Learning Systems",
    authors: ["김철수", "이영희"],
    abstract:
      "This paper explores the implementation of AI-driven personalized learning systems in educational environments...",
    source: "Journal of Educational Technology",
    publishedAt: "2024-01-01",
    url: "https://example.com/paper1",
  },
  {
    id: "2",
    title: "The Future of Online Education",
    authors: ["박민수"],
    abstract: "An analysis of emerging trends in online education and their impact on traditional learning methods...",
    source: "Educational Research Quarterly",
    publishedAt: "2023-12-15",
    url: "https://example.com/paper2",
  },
]

export const mockCommunityPosts: CommunityPost[] = [
  {
    id: "1",
    title: "새로운 학습 방법론 제안",
    summary: "효과적인 온라인 학습을 위한 새로운 접근법을 제안합니다.",
    author: "김학습",
    votes: 15,
    createdAt: "2024-01-12",
  },
  {
    id: "2",
    title: "교육 플랫폼 개선 아이디어",
    summary: "사용자 경험을 향상시킬 수 있는 플랫폼 개선 방안입니다.",
    author: "이개발",
    votes: 8,
    createdAt: "2024-01-10",
  },
]

// API functions
export const fetchArticles = async (params: ArticlesParams) => {
  const response = await api.get("/axpress/articles", { params })
  return response.data
}

export const fetchArticle = async (id: string): Promise<Article> => {
  const response = await api.get(`/axpress/articles/${id}`)
  return response.data
}

export const fetchPapers = async (params: PapersParams) => {
  const queryParams = {
    ...params,
    tags: params.tags?.join(","),
  }
  const response = await api.get("/axpress/papers", { params: queryParams })
  return response.data
}

export const fetchCommunity = async (params: CommunityParams) => {
  const response = await api.get("/axpress/community", { params })
  return response.data
}
