"use client"

import { CATEGORY_LABELS, type ArticleCategory } from "@/types/axpress"
import { cn } from "@/lib/utils"

interface CategoryTabsProps {
  activeCategory: ArticleCategory
  onCategoryChange: (category: ArticleCategory) => void
}

export function CategoryTabs({ activeCategory, onCategoryChange }: CategoryTabsProps) {
  const categories = Object.entries(CATEGORY_LABELS) as [ArticleCategory, string][]

  return (
    <div className="flex flex-wrap gap-2">
      {categories.map(([category, label]) => (
        <button
          key={category}
          type="button"
          onClick={() => onCategoryChange(category)}
          className={cn(
            "ax-focus-ring rounded-lg px-4 py-2 text-sm font-medium transition-colors duration-200",
            activeCategory === category
              ? "ax-button-primary"
              : "border border-[var(--ax-border)] bg-[var(--ax-surface)] text-[var(--ax-fg)] hover:bg-[var(--ax-border)]",
          )}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
