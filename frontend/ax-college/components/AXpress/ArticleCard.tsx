import Link from "next/link"
import { Calendar, Eye } from "lucide-react"
import type { ArticleCard as ArticleCardType } from "@/types/axpress"
import { CATEGORY_LABELS } from "@/types/axpress"
import { cn } from "@/lib/utils"

interface ArticleCardProps {
  article: ArticleCardType
  className?: string
}

export function ArticleCard({ article, className }: ArticleCardProps) {
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
    <Link
      href={`/axpress/${article.id}`}
      className={cn("ax-card ax-focus-ring group block p-6 transition-all duration-200 hover:shadow-lg", className)}
    >
      <div className="mb-3 flex items-center justify-between">
        <span
          className={cn(
            "rounded-full px-3 py-1 text-xs font-medium",
            article.category === "news" && "bg-blue-100 text-blue-800",
            article.category === "notice" && "bg-red-100 text-red-800",
            article.category === "event" && "bg-green-100 text-green-800",
            article.category === "guide" && "bg-purple-100 text-purple-800",
          )}
        >
          {CATEGORY_LABELS[article.category]}
        </span>
        <div className="flex items-center gap-4 text-xs text-[var(--ax-fg)]/60">
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {formatDate(article.publishedAt)}
          </div>
          <div className="flex items-center gap-1">
            <Eye className="h-3 w-3" />
            {formatViews(article.views)}
          </div>
        </div>
      </div>

      <h3 className="mb-2 text-lg font-semibold text-[var(--ax-fg)] group-hover:text-[var(--ax-accent)]">
        {article.title}
      </h3>

      {article.summary && <p className="mb-3 text-pretty text-sm text-[var(--ax-fg)]/70">{article.summary}</p>}

      {article.tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {article.tags.map((tag) => (
            <span key={tag} className="rounded-md bg-[var(--ax-border)] px-2 py-1 text-xs text-[var(--ax-fg)]/70">
              #{tag}
            </span>
          ))}
        </div>
      )}
    </Link>
  )
}
