"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import type { NavItem as NavItemType } from "@/types/navigation"
import { cn } from "@/lib/utils"

interface NavItemProps {
  item: NavItemType
  onHover?: () => void
  onLeave?: () => void
}

export function NavItem({ item, onHover, onLeave }: NavItemProps) {
  const pathname = usePathname()

  const isActive = (): boolean => {
    if (item.path === "/" && pathname === "/") return true
    if (item.path !== "/" && pathname.startsWith(item.path)) return true
    return false
  }

  return (
    <div className="relative" onMouseEnter={onHover} onMouseLeave={onLeave}>
      <Link
        href={item.path}
        className={cn(
          "ax-nav-link ax-focus-ring relative px-3 py-2 text-sm font-medium transition-colors duration-200",
          isActive() && "active",
        )}
      >
        {item.label}
      </Link>
    </div>
  )
}
