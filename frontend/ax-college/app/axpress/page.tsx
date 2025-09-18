"use client"

import { Suspense } from "react"
import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"
import { CategoryTabs } from "@/components/AXpress/CategoryTabs"
import { SearchBar } from "@/components/AXpress/SearchBar"
import { ArticleCard } from "@/components/AXpress/ArticleCard"
import { EmptyState } from "@/components/UI/EmptyState"
import { useArticles } from "@/hooks/use-axpress"
import type { ArticleCategory } from "@/types/axpress"

function AXpressContent() {
  const { articles, isLoading, error, category, query, updateFilters } = useArticles()

  const handleCategoryChange = (newCategory: ArticleCategory) => {
    updateFilters({ category: newCategory, page: 1 })
  }

  const handleSearchChange = (newQuery: string) => {
    updateFilters({ q: newQuery, page: 1 })
  }

  if (error) {
    return (
      <EmptyState title="오류가 발생했습니다" description={error} action={{ label: "다시 시도", href: "/axpress" }} />
    )
  }

  return (
    <PageLayout>
      <PageHeader title="AXpress" description="최신 뉴스, 공지사항, 이벤트 및 가이드를 확인하세요." />

      <div className="mb-8 space-y-6">
        <CategoryTabs activeCategory={category} onCategoryChange={handleCategoryChange} />
        <SearchBar value={query} onChange={handleSearchChange} className="max-w-md" />
      </div>

      {isLoading ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="ax-card h-48 animate-pulse bg-[var(--ax-border)]" />
          ))}
        </div>
      ) : articles.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {articles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
      ) : (
        <EmptyState
          title="콘텐츠가 없습니다"
          description={query ? "검색 조건에 맞는 콘텐츠를 찾을 수 없습니다." : "아직 등록된 콘텐츠가 없습니다."}
          action={{ label: "전체 보기", href: "/axpress" }}
        />
      )}
    </PageLayout>
  )
}

export default function AXpressPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <AXpressContent />
    </Suspense>
  )
}
