import type React from "react"
import { cn } from "@/lib/utils"

interface PageHeaderProps {
  title: string
  description?: string
  children?: React.ReactNode
  className?: string
}

export function PageHeader({ title, description, children, className }: PageHeaderProps) {
  return (
    <div className={cn("mb-6 md:mb-8", className)}>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <h1 className="text-balance text-2xl font-bold text-[var(--ax-fg)] md:text-3xl lg:text-4xl">{title}</h1>
          {description && <p className="mt-2 text-pretty text-base text-[var(--ax-fg)]/80 md:text-lg">{description}</p>}
        </div>
        {children && <div className="flex flex-shrink-0 items-center gap-3">{children}</div>}
      </div>
    </div>
  )
}
