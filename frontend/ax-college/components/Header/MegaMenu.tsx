"use client"

import { useEffect, useRef, useState } from "react"
import Link from "next/link"
import type { NavChild } from "@/types/navigation"
import { cn } from "@/lib/utils"

interface MegaMenuProps {
  items: NavChild[]
  onMouseEnter: () => void
  onMouseLeave: () => void
  onClose: () => void
  anchorElement?: HTMLElement | null
}

export function MegaMenu({ items, onMouseEnter, onMouseLeave, onClose, anchorElement }: MegaMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState({ top: 0, left: 0 })

  useEffect(() => {
    if (anchorElement && menuRef.current) {
      const anchorRect = anchorElement.getBoundingClientRect()
      const menuRect = menuRef.current.getBoundingClientRect()
      const windowWidth = window.innerWidth

      // Default positioning: below the nav item with 8px gap
      const top = anchorRect.bottom + 8
      let left = anchorRect.left

      // Panel width constraints: min 220px ~ max 320px
      const panelWidth = Math.min(Math.max(220, menuRect.width), 320)

      // Right overflow correction
      if (left + panelWidth > windowWidth - 16) {
        left = windowWidth - panelWidth - 16
      }

      setPosition({ top, left })
    }
  }, [anchorElement, items])

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose()
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [onClose])

  return (
    <div
      ref={menuRef}
      className="fixed z-50 animate-in fade-in-0 zoom-in-95 slide-in-from-top-2"
      style={{
        top: `${position.top}px`,
        left: `${position.left}px`,
        minWidth: "220px",
        maxWidth: "320px",
      }}
      onMouseEnter={onMouseEnter}
      onMouseLeave={onMouseLeave}
    >
      <div className="ax-card rounded-xl p-4 shadow-[0_8px_24px_rgba(0,0,0,0.08)]">
        <div className="space-y-2">
          {items.map((item, index) => (
            <Link
              key={item.path}
              href={item.path}
              className={cn(
                "ax-focus-ring block rounded-lg px-3 py-2 text-sm font-medium text-[var(--ax-fg)] transition-colors duration-200",
                "hover:bg-[var(--ax-border)] hover:text-[var(--ax-accent)]",
              )}
              onClick={onClose}
              tabIndex={0}
            >
              <div className="font-medium">{item.label}</div>
              {item.description && <div className="mt-1 text-xs text-[var(--ax-fg)]/70">{item.description}</div>}
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
