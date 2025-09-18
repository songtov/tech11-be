"use client"

import type React from "react"
import { useRequireAuth } from "@/hooks/use-auth"
import { EmptyState } from "@/components/UI/EmptyState"

interface ProtectedRouteProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function ProtectedRoute({ children, fallback }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useRequireAuth()

  if (isLoading) {
    return (
      fallback || (
        <div className="flex min-h-[400px] items-center justify-center">
          <div className="ax-card p-8 text-center">
            <div className="mb-4 h-8 w-8 animate-spin rounded-full border-2 border-[var(--ax-accent)] border-t-transparent mx-auto" />
            <p className="text-[var(--ax-fg)]/70">인증 확인 중...</p>
          </div>
        </div>
      )
    )
  }

  if (!isAuthenticated) {
    return (
      <EmptyState
        title="로그인이 필요합니다"
        description="이 페이지에 접근하려면 로그인이 필요합니다."
        action={{ label: "홈으로", href: "/" }}
      />
    )
  }

  return <>{children}</>
}
