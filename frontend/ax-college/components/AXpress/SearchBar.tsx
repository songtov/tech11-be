"use client"

import { useState, useEffect } from "react"
import { Search, X } from "lucide-react"
import { cn } from "@/lib/utils"

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
}

export function SearchBar({ value, onChange, placeholder = "검색어를 입력하세요...", className }: SearchBarProps) {
  const [localValue, setLocalValue] = useState(value)

  useEffect(() => {
    setLocalValue(value)
  }, [value])

  useEffect(() => {
    const timer = setTimeout(() => {
      onChange(localValue)
    }, 300)

    return () => clearTimeout(timer)
  }, [localValue, onChange])

  return (
    <div className={cn("relative", className)}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--ax-fg)]/50" />
        <input
          type="text"
          value={localValue}
          onChange={(e) => setLocalValue(e.target.value)}
          placeholder={placeholder}
          className="ax-focus-ring w-full rounded-lg border border-[var(--ax-border)] bg-[var(--ax-surface)] py-2 pl-10 pr-10 text-sm text-[var(--ax-fg)] placeholder-[var(--ax-fg)]/50"
        />
        {localValue && (
          <button
            type="button"
            onClick={() => {
              setLocalValue("")
              onChange("")
            }}
            className="ax-focus-ring absolute right-3 top-1/2 -translate-y-1/2 rounded p-1 text-[var(--ax-fg)]/50 hover:text-[var(--ax-fg)]"
            aria-label="검색어 지우기"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}
