import Link from "next/link"
import { Home } from "lucide-react"
import { cn } from "@/lib/utils"

interface EmptyStateProps {
  title?: string
  description?: string
  action?: {
    label: string
    href: string
  }
  className?: string
}

export function EmptyState({
  title = "콘텐츠가 없습니다",
  description = "요청하신 내용을 찾을 수 없습니다.",
  action = { label: "홈으로", href: "/" },
  className,
}: EmptyStateProps) {
  return (
    <div className={cn("ax-card flex flex-col items-center justify-center p-12 text-center", className)}>
      <div className="mb-4 rounded-full bg-[var(--ax-border)] p-4">
        <Home className="h-8 w-8 text-[var(--ax-fg)]/50" />
      </div>
      <h3 className="mb-2 text-xl font-semibold text-[var(--ax-fg)]">{title}</h3>
      <p className="mb-6 text-[var(--ax-fg)]/70">{description}</p>
      <Link
        href={action.href}
        className="ax-button-primary ax-focus-ring inline-flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors"
      >
        {action.label}
      </Link>
    </div>
  )
}
