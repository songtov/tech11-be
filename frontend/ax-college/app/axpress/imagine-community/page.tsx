"use client"

import { Suspense } from "react"
import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"
import { SearchBar } from "@/components/AXpress/SearchBar"
import { EmptyState } from "@/components/UI/EmptyState"
import { useCommunity } from "@/hooks/use-axpress"
import { useAXToast } from "@/hooks/use-toast"
import { ThumbsUp, Calendar, User, Plus } from "lucide-react"
import { cn } from "@/lib/utils"

function CommunityContent() {
  const { posts, isLoading, error, query, sort, updateFilters } = useCommunity()
  const { showPreparingToast } = useAXToast()

  const handleSearchChange = (newQuery: string) => {
    updateFilters({ q: newQuery, page: 1 })
  }

  const handleSortChange = (newSort: "recent" | "popular") => {
    updateFilters({ sort: newSort, page: 1 })
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
        action={{ label: "다시 시도", href: "/axpress/imagine-community" }}
      />
    )
  }

  return (
    <PageLayout>
      <PageHeader title="Imagine Community" description="창의적인 아이디어와 제안을 공유하고 토론하세요.">
        <button
          type="button"
          onClick={() => showPreparingToast("글 작성 기능")}
          className="ax-button-primary ax-focus-ring inline-flex items-center gap-2 px-4 py-2 text-sm font-medium"
        >
          <Plus className="h-4 w-4" />글 작성
        </button>
      </PageHeader>

      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <SearchBar
          value={query}
          onChange={handleSearchChange}
          placeholder="제목, 내용으로 검색..."
          className="max-w-md"
        />

        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => handleSortChange("recent")}
            className={cn(
              "ax-focus-ring rounded-lg px-4 py-2 text-sm font-medium transition-colors duration-200",
              sort === "recent"
                ? "ax-button-primary"
                : "border border-[var(--ax-border)] bg-[var(--ax-surface)] text-[var(--ax-fg)] hover:bg-[var(--ax-border)]",
            )}
          >
            최신순
          </button>
          <button
            type="button"
            onClick={() => handleSortChange("popular")}
            className={cn(
              "ax-focus-ring rounded-lg px-4 py-2 text-sm font-medium transition-colors duration-200",
              sort === "popular"
                ? "ax-button-primary"
                : "border border-[var(--ax-border)] bg-[var(--ax-surface)] text-[var(--ax-fg)] hover:bg-[var(--ax-border)]",
            )}
          >
            인기순
          </button>
        </div>
      </div>

      {isLoading ? (
        <div className="space-y-6">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="ax-card h-32 animate-pulse bg-[var(--ax-border)]" />
          ))}
        </div>
      ) : posts.length > 0 ? (
        <div className="space-y-6">
          {posts.map((post) => (
            <div
              key={post.id}
              className="ax-card ax-focus-ring cursor-pointer p-6 transition-all duration-200 hover:shadow-lg"
              onClick={() => showPreparingToast("게시글 상세 보기")}
            >
              <div className="mb-3 flex items-start justify-between">
                <h3 className="text-xl font-semibold text-[var(--ax-fg)] hover:text-[var(--ax-accent)]">
                  {post.title}
                </h3>
                <div className="flex items-center gap-1 text-[var(--ax-accent)]">
                  <ThumbsUp className="h-4 w-4" />
                  <span className="text-sm font-medium">{post.votes}</span>
                </div>
              </div>

              <p className="mb-3 text-pretty text-[var(--ax-fg)]/80">{post.summary}</p>

              <div className="flex items-center gap-4 text-sm text-[var(--ax-fg)]/60">
                <div className="flex items-center gap-1">
                  <User className="h-4 w-4" />
                  {post.author}
                </div>
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  {formatDate(post.createdAt)}
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState
          title="게시글이 없습니다"
          description={query ? "검색 조건에 맞는 게시글을 찾을 수 없습니다." : "아직 등록된 게시글이 없습니다."}
          action={{ label: "전체 보기", href: "/axpress/imagine-community" }}
        />
      )}
    </PageLayout>
  )
}

export default function ImagineCommunityPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <CommunityContent />
    </Suspense>
  )
}
