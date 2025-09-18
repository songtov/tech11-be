"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { X, ChevronDown, ChevronRight } from "lucide-react"
import { NAV_DATA, type NavItem } from "@/types/navigation"
import { useAuth } from "@/hooks/use-auth"
import { cn } from "@/lib/utils"

interface MobileMenuProps {
  isOpen: boolean
  onClose: () => void
}

export function MobileMenu({ isOpen, onClose }: MobileMenuProps) {
  const [expandedMenus, setExpandedMenus] = useState<Set<string>>(new Set())
  const pathname = usePathname()
  const { isAuthenticated } = useAuth()

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden"
    } else {
      document.body.style.overflow = "unset"
    }

    return () => {
      document.body.style.overflow = "unset"
    }
  }, [isOpen])

  const toggleMenu = (menuKey: string) => {
    const newExpanded = new Set(expandedMenus)
    if (newExpanded.has(menuKey)) {
      newExpanded.delete(menuKey)
    } else {
      newExpanded.add(menuKey)
    }
    setExpandedMenus(newExpanded)
  }

  const isActiveRoute = (item: NavItem): boolean => {
    if (item.path === "/" && pathname === "/") return true
    if (item.path !== "/" && pathname.startsWith(item.path)) return true
    return false
  }

  const handleLinkClick = () => {
    onClose()
    setExpandedMenus(new Set())
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 lg:hidden">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50" onClick={onClose} />

      {/* Menu Panel */}
      <div className="fixed right-0 top-0 h-full w-80 max-w-[90vw] bg-[var(--ax-surface)] shadow-xl">
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-[var(--ax-border)] p-4">
            <h2 className="text-lg font-semibold text-[var(--ax-fg)]">메뉴</h2>
            <button
              type="button"
              onClick={onClose}
              className="ax-focus-ring rounded-lg p-2 text-[var(--ax-fg)]/60 hover:bg-[var(--ax-border)] hover:text-[var(--ax-fg)]"
              aria-label="메뉴 닫기"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4">
            <div className="space-y-2">
              {NAV_DATA.map((item) => {
                // Skip protected routes if not authenticated
                if (item.protected && !isAuthenticated) {
                  return null
                }

                const hasChildren = item.children && item.children.length > 0
                const isExpanded = expandedMenus.has(item.key)
                const isActive = isActiveRoute(item)

                return (
                  <div key={item.key}>
                    {hasChildren ? (
                      <button
                        type="button"
                        onClick={() => toggleMenu(item.key)}
                        className={cn(
                          "ax-focus-ring flex w-full items-center justify-between rounded-lg px-3 py-2 text-left text-sm font-medium transition-colors",
                          isActive
                            ? "bg-[var(--ax-accent)]/10 text-[var(--ax-accent)]"
                            : "text-[var(--ax-fg)] hover:bg-[var(--ax-border)]",
                        )}
                      >
                        {item.label}
                        {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                      </button>
                    ) : (
                      <Link
                        href={item.path}
                        onClick={handleLinkClick}
                        className={cn(
                          "ax-focus-ring block rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                          isActive
                            ? "bg-[var(--ax-accent)]/10 text-[var(--ax-accent)]"
                            : "text-[var(--ax-fg)] hover:bg-[var(--ax-border)]",
                        )}
                      >
                        {item.label}
                      </Link>
                    )}

                    {/* Submenu */}
                    {hasChildren && isExpanded && (
                      <div className="ml-4 mt-2 space-y-1 border-l border-[var(--ax-border)] pl-4">
                        {item.children?.map((child) => (
                          <Link
                            key={child.path}
                            href={child.path}
                            onClick={handleLinkClick}
                            className={cn(
                              "ax-focus-ring block rounded-lg px-3 py-2 text-sm transition-colors",
                              pathname === child.path
                                ? "bg-[var(--ax-accent)]/10 text-[var(--ax-accent)]"
                                : "text-[var(--ax-fg)]/80 hover:bg-[var(--ax-border)] hover:text-[var(--ax-fg)]",
                            )}
                          >
                            {child.label}
                          </Link>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          </nav>
        </div>
      </div>
    </div>
  )
}
