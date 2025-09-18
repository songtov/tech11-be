"use client"

import { useState, useEffect, useRef } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Search, Menu, HelpCircle } from "lucide-react"
import { NAV_DATA, type NavItem } from "@/types/navigation"
import { MegaMenu } from "./MegaMenu"
import { FullMegaMenu } from "./FullMegaMenu"
import { MobileMenu } from "./MobileMenu"
import { UserMenu } from "./UserMenu"
import { useAXToast } from "@/hooks/use-toast"
import { cn } from "@/lib/utils"

export function Header() {
  const [activeMenu, setActiveMenu] = useState<string | null>(null)
  const [isFullMenuOpen, setIsFullMenuOpen] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const [isScrolled, setIsScrolled] = useState(false)
  const pathname = usePathname()
  const { showPreparingToast } = useAXToast()
  const headerRef = useRef<HTMLElement>(null)
  const timeoutRef = useRef<NodeJS.Timeout>()
  const fullMenuTimeoutRef = useRef<NodeJS.Timeout>()
  const navItemRefs = useRef<{ [key: string]: HTMLAnchorElement | null }>({})

  // Handle scroll effect
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10)
    }

    window.addEventListener("scroll", handleScroll)
    return () => window.removeEventListener("scroll", handleScroll)
  }, [])

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setActiveMenu(null)
        setIsFullMenuOpen(false)
        setIsMobileMenuOpen(false)
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [])

  const handleHeaderMouseEnter = () => {
    if (fullMenuTimeoutRef.current) {
      clearTimeout(fullMenuTimeoutRef.current)
    }
    // Only show on desktop
    if (window.innerWidth >= 1024) {
      setIsFullMenuOpen(true)
    }
  }

  const handleHeaderMouseLeave = () => {
    fullMenuTimeoutRef.current = setTimeout(() => {
      setIsFullMenuOpen(false)
    }, 200)
  }

  const handleFullMenuMouseEnter = () => {
    if (fullMenuTimeoutRef.current) {
      clearTimeout(fullMenuTimeoutRef.current)
    }
  }

  const handleFullMenuMouseLeave = () => {
    fullMenuTimeoutRef.current = setTimeout(() => {
      setIsFullMenuOpen(false)
    }, 200)
  }

  const handleMenuHover = (menuKey: string) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setActiveMenu(menuKey)
  }

  const handleMenuLeave = () => {
    timeoutRef.current = setTimeout(() => {
      setActiveMenu(null)
    }, 200)
  }

  const handleMegaMenuHover = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
  }

  const isActiveRoute = (item: NavItem): boolean => {
    if (item.path === "/" && pathname === "/") return true
    if (item.path !== "/" && pathname.startsWith(item.path)) return true
    return false
  }

  return (
    <>
      <header
        ref={headerRef}
        className={cn(
          "ax-header sticky top-0 z-40 transition-all duration-200",
          isScrolled && "shadow-sm backdrop-blur-md",
        )}
        onMouseEnter={handleHeaderMouseEnter}
        onMouseLeave={handleHeaderMouseLeave}
      >
        <nav
          className="mx-auto flex h-[var(--header-height)] max-w-7xl items-center justify-between px-4 md:px-6 lg:px-8"
          aria-label="AX College 메인 네비게이션"
        >
          {/* Logo */}
          <Link href="/" className="ax-focus-ring text-lg font-bold text-[var(--ax-fg)] md:text-2xl lg:text-2xl">
            AX <span className="text-[var(--ax-accent)]">College</span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden items-center space-x-2 lg:flex xl:space-x-8">
            {NAV_DATA.map((item) => {
              return (
                <div
                  key={item.key}
                  className="relative"
                  onMouseEnter={() => item.children && handleMenuHover(item.key)}
                  onMouseLeave={handleMenuLeave}
                >
                  <Link
                    ref={(el) => {
                      navItemRefs.current[item.key] = el
                    }}
                    href={item.path}
                    className={cn(
                      "ax-nav-link ax-focus-ring relative px-8 py-6 text-sm font-medium transition-colors duration-200 xl:px-3",
                      isActiveRoute(item) && "active",
                    )}
                    onFocus={() => item.children && setActiveMenu(item.key)}
                  >
                    {item.label}
                  </Link>

                  {/* Individual MegaMenu (hidden when full menu is open) */}
                  {item.children && activeMenu === item.key && !isFullMenuOpen && (
                    <MegaMenu
                      items={item.children}
                      onMouseEnter={handleMegaMenuHover}
                      onMouseLeave={handleMenuLeave}
                      onClose={() => setActiveMenu(null)}
                      anchorElement={navItemRefs.current[item.key]}
                    />
                  )}
                </div>
              )
            })}
          </div>

          {/* Utility Icons and User Menu */}
          <div className="flex items-center-[ml-5] space-x-2 md:space-x-3">
            <button
              type="button"
              className="ax-focus-ring rounded-lg p-3 text-[var(--ax-fg)] transition-colors hover:bg-[var(--ax-border)]"
              onClick={() => showPreparingToast("검색 기능")}
              aria-label="검색"
            >
              <Search className="h-4 w-4 md:h-5 md:w-5" />
            </button>

            <button
              type="button"
              className="ax-focus-ring rounded-lg p-3 text-[var(--ax-fg)] transition-colors hover:bg-[var(--ax-border)] lg:hidden"
              onClick={() => setIsMobileMenuOpen(true)}
              aria-label="메뉴"
            >
              <Menu className="h-4 w-4 md:h-5 md:w-5" />
            </button>

            <button
              type="button"
              className="ax-focus-ring ax-helpdesk-icon rounded-lg p-3 transition-colors hover:bg-[var(--ax-border)]"
              onClick={() => showPreparingToast("Help Desk")}
              aria-label="Help Desk"
            >
              <HelpCircle className="h-3 w-3 md:h-4 md:w-4" />
            </button>

            {/* UserMenu component for authentication */}
            <UserMenu />
          </div>
        </nav>
      </header>

      <FullMegaMenu
        isOpen={isFullMenuOpen}
        onMouseEnter={handleFullMenuMouseEnter}
        onMouseLeave={handleFullMenuMouseLeave}
        onClose={() => setIsFullMenuOpen(false)}
      />

      {/* Mobile Menu */}
      <MobileMenu isOpen={isMobileMenuOpen} onClose={() => setIsMobileMenuOpen(false)} />
    </>
  )
}
