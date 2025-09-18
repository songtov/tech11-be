"use client"

import { useState, useRef, useEffect } from "react"
import { useAuth } from "@/hooks/use-auth"
import { LoginModal } from "@/components/Auth/LoginModal"
import { User, LogOut, Settings } from "lucide-react"
import Link from "next/link"

export function UserMenu() {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [isLoginModalOpen, setIsLoginModalOpen] = useState(false)
  const { user, logout, isAuthenticated } = useAuth()
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false)
      }
    }

    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  if (!isAuthenticated) {
    return (
      <>
        <button
          type="button"
          onClick={() => setIsLoginModalOpen(true)}
          className="ax-button-primary ax-focus-ring px-4 py-2 text-sm font-medium"
        >
          로그인
        </button>
        <LoginModal isOpen={isLoginModalOpen} onClose={() => setIsLoginModalOpen(false)} />
      </>
    )
  }

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsDropdownOpen(!isDropdownOpen)}
        className="ax-focus-ring flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-[var(--ax-fg)] transition-colors hover:bg-[var(--ax-border)]"
        aria-expanded={isDropdownOpen}
        aria-haspopup="true"
      >
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--ax-accent)] text-white">
          <User className="h-4 w-4" />
        </div>
        <span className="hidden sm:block">{user?.name}</span>
      </button>

      {isDropdownOpen && (
        <div className="absolute right-0 top-full z-50 mt-2 w-48 animate-in fade-in-0 zoom-in-95 slide-in-from-top-2">
          <div className="ax-card p-2 shadow-lg">
            <div className="mb-2 border-b border-[var(--ax-border)] px-3 py-2">
              <p className="text-sm font-medium text-[var(--ax-fg)]">{user?.name}</p>
              <p className="text-xs text-[var(--ax-fg)]/60">{user?.email}</p>
            </div>

            <Link
              href="/my"
              className="ax-focus-ring flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-[var(--ax-fg)] transition-colors hover:bg-[var(--ax-border)]"
              onClick={() => setIsDropdownOpen(false)}
            >
              <Settings className="h-4 w-4" />
              My Page
            </Link>

            <button
              type="button"
              onClick={() => {
                logout()
                setIsDropdownOpen(false)
              }}
              className="ax-focus-ring flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-[var(--ax-fg)] transition-colors hover:bg-[var(--ax-border)]"
            >
              <LogOut className="h-4 w-4" />
              로그아웃
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
