"use client"

import { Suspense } from "react"
import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"
import { SearchBar } from "@/components/AXpress/SearchBar"
import { EmptyState } from "@/components/UI/EmptyState"
import { usePapers } from "@/hooks/use-axpress"
import { ExternalLink, Calendar, User } from "lucide-react"
import Link from "next/link"

function PapersContent() {
  const { papers, isLoading, error, query, updateFilters } = usePapers()

  const handleSearchChange = (newQuery: string) => {
    updateFilters({ q: newQuery, page: 1 })
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

  if (error) {
    return (
      <EmptyState
        title="오류가 발생했습니다"
        description={error}
        action={{ label: "다시 시도", href: "/axpress/papers" }}
      />
    )
  }

  return (
    <PageLayout>
      <PageHeader title="최신 논문 탐색" description="교육 관련 최신 논문과 연구 자료를 탐색하세요." />

      <div className="mb-8">
        <SearchBar
          value={query}
          onChange={handleSearchChange}
          placeholder="논문 제목, 저자, 키워드로 검색..."
          className="max-w-lg"
        />
      </div>

      {isLoading ? (
        <div className="space-y-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="ax-card h-32 animate-pulse bg-[var(--ax-border)]" />
          ))}
        </div>
      ) : papers.length > 0 ? (
        <div className="space-y-6">
          {papers.map((paper) => (
            <div key={paper.id} className="ax-card p-6">
              <div className="mb-3 flex items-start justify-between">
                <h3 className="text-xl font-semibold text-[var(--ax-fg)]">{paper.title}</h3>
                <Link
                  href={paper.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="ax-focus-ring rounded-lg p-2 text-[var(--ax-accent)] transition-colors hover:bg-[var(--ax-border)]"
                  aria-label="원문 보기"
                >
                  <ExternalLink className="h-5 w-5" />
                </Link>
              </div>

              <div className="mb-3 flex flex-wrap items-center gap-4 text-sm text-[var(--ax-fg)]/60">
                <div className="flex items-center gap-1">
                  <User className="h-4 w-4" />
                  {paper.authors.join(", ")}
                </div>
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  {formatDate(paper.publishedAt)}
                </div>
                <span className="rounded-full bg-[var(--ax-accent)]/10 px-3 py-1 text-xs font-medium text-[var(--ax-accent)]">
                  {paper.source}
                </span>
              </div>

              <p className="text-pretty leading-relaxed text-[var(--ax-fg)]/80">{paper.abstract}</p>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          title="논문이 없습니다"
          description={query ? "검색 조건에 맞는 논문을 찾을 수 없습니다." : "아직 등록된 논문이 없습니다."}
          action={{ label: "전체 보기", href: "/axpress/papers" }}
        />
      )}
    </PageLayout>
  )
}

export default function PapersPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <PapersContent />
    </Suspense>
  )
}
