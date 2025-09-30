import { z } from "zod"

export const ArticleCategory = z.enum(["all", "news", "notice", "event", "guide"])
export type ArticleCategory = z.infer<typeof ArticleCategory>

export const ArticleCard = z.object({
  id: z.string(),
  title: z.string(),
  summary: z.string().optional(),
  category: ArticleCategory,
  tags: z.array(z.string()).default([]),
  thumb: z.string().nullable(),
  publishedAt: z.string(),
  views: z.number(),
})
export type ArticleCard = z.infer<typeof ArticleCard>

export const Article = ArticleCard.extend({
  body: z.string(),
})
export type Article = z.infer<typeof Article>

export const Paper = z.object({
  id: z.string(),
  title: z.string(),
  authors: z.array(z.string()),
  abstract: z.string(),
  source: z.string(),
  publishedAt: z.string(),
  url: z.string().url(),
})
export type Paper = z.infer<typeof Paper>

export const CommunityPost = z.object({
  id: z.string(),
  title: z.string(),
  summary: z.string(),
  author: z.string(),
  votes: z.number().default(0),
  createdAt: z.string(),
})
export type CommunityPost = z.infer<typeof CommunityPost>

export const CATEGORY_LABELS: Record<ArticleCategory, string> = {
  all: "전체",
  news: "뉴스",
  notice: "공지",
  event: "이벤트",
  guide: "가이드",
}
