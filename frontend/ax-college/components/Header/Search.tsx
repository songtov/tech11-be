"use client"

import type React from "react"
import { useState } from "react"
import { SearchIcon, X } from "lucide-react"
import { useAXToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"

interface SearchProps {
  className?: string
}

export function Search({ className }: SearchProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [query, setQuery] = useState("")
  const { showPreparingToast } = useAXToast()

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    showPreparingToast("검색 기능")
    setIsOpen(false)
    setQuery("")
  }

  return (
    <div className={cn("relative", className)}>
      {!isOpen ? (
        <button
          type="button"
          className="ax-focus-ring rounded-lg p-2 text-[var(--ax-fg)] transition-colors hover:bg-[var(--ax-border)]"
          onClick={() => setIsOpen(true)}
          aria-label="검색 열기"
        >
          <SearchIcon className="h-5 w-5" />
        </button>
      ) : (
        <form onSubmit={handleSearch} className="flex items-center">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="검색어를 입력하세요..."
              className="ax-focus-ring w-64 rounded-lg border border-[var(--ax-border)] bg-[var(--ax-surface)] px-4 py-2 pl-10 text-sm text-[var(--ax-fg)] placeholder-[var(--ax-fg)]/50"
              autoFocus
            />
            <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--ax-fg)]/50" />
          </div>
          <button
            type="button"
            className="ax-focus-ring ml-2 rounded-lg p-2 text-[var(--ax-fg)] transition-colors hover:bg-[var(--ax-border)]"
            onClick={() => {
              setIsOpen(false)
              setQuery("")
            }}
            aria-label="검색 닫기"
          >
            <X className="h-4 w-4" />
          </button>
        </form>
      )}
    </div>
  )
}
