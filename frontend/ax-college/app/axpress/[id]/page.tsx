import { PageLayout } from "@/components/Layout/PageLayout"
import { EmptyState } from "@/components/UI/EmptyState"
import { mockArticles } from "@/services/axpress-data"
import { Calendar, Eye, ArrowLeft } from "lucide-react"
import Link from "next/link"
import { CATEGORY_LABELS } from "@/types/axpress"
import { cn } from "@/lib/utils"

interface ArticleDetailPageProps {
  params: {
    id: string
  }
}

export default function ArticleDetailPage({ params }: ArticleDetailPageProps) {
  const article = mockArticles.find((a) => a.id === params.id)

  if (!article) {
    return (
      <PageLayout>
        <EmptyState
          title="게시글을 찾을 수 없습니다"
          description="요청하신 게시글이 존재하지 않거나 삭제되었습니다."
          action={{ label: "목록으로", href: "/axpress" }}
        />
      </PageLayout>
    )
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("ko-KR", {
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

  const formatViews = (views: number) => {
    if (views >= 1000) {
      return `${(views / 1000).toFixed(1)}k`
    }
    return views.toString()
  }

  return (
    <PageLayout>
      <div className="mb-6">
        <Link
          href="/axpress"
          className="ax-focus-ring inline-flex items-center gap-2 text-sm text-[var(--ax-accent)] hover:underline"
        >
          <ArrowLeft className="h-4 w-4" />
          목록으로 돌아가기
        </Link>
      </div>

      <article className="ax-card p-8">
        <header className="mb-8">
          <div className="mb-4 flex items-center justify-between">
            <span
              className={cn(
                "rounded-full px-3 py-1 text-sm font-medium",
                article.category === "news" && "bg-blue-100 text-blue-800",
                article.category === "notice" && "bg-red-100 text-red-800",
                article.category === "event" && "bg-green-100 text-green-800",
                article.category === "guide" && "bg-purple-100 text-purple-800",
              )}
            >
              {CATEGORY_LABELS[article.category]}
            </span>
            <div className="flex items-center gap-4 text-sm text-[var(--ax-fg)]/60">
              <div className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                {formatDate(article.publishedAt)}
              </div>
              <div className="flex items-center gap-1">
                <Eye className="h-4 w-4" />
                {formatViews(article.views)}
              </div>
            </div>
          </div>

          <h1 className="mb-4 text-balance text-3xl font-bold text-[var(--ax-fg)] md:text-4xl">{article.title}</h1>

          {article.summary && <p className="text-pretty text-lg text-[var(--ax-fg)]/80">{article.summary}</p>}
        </header>

        <div className="prose prose-lg max-w-none">
          <p className="leading-relaxed text-[var(--ax-fg)]">
            이곳에 게시글의 본문 내용이 표시됩니다. 현재는 샘플 데이터를 사용하고 있으며, 실제 구현 시에는 리치 텍스트
            에디터로 작성된 내용이 렌더링됩니다.
          </p>
          <p className="leading-relaxed text-[var(--ax-fg)]">
            게시글 내용은 HTML 형태로 저장되어 안전하게 렌더링되며, 이미지, 링크, 목록 등 다양한 형태의 콘텐츠를 지원할
            수 있습니다.
          </p>
        </div>

        {article.tags.length > 0 && (
          <footer className="mt-8 pt-6 border-t border-[var(--ax-border)]">
            <div className="flex flex-wrap gap-2">
              {article.tags.map((tag) => (
                <span key={tag} className="rounded-md bg-[var(--ax-border)] px-3 py-1 text-sm text-[var(--ax-fg)]/70">
                  #{tag}
                </span>
              ))}
            </div>
          </footer>
        )}
      </article>
    </PageLayout>
  )
}
