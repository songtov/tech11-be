"use client"

import { ProtectedRoute } from "@/components/Auth/ProtectedRoute"
import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"

function LeaderCoachingContent() {
  return (
    <PageLayout>
      <PageHeader title="육성리더 코칭" description="리더십 코칭 프로그램 현황을 확인하세요." />

      <div className="ax-card p-8 text-center">
        <h2 className="mb-4 text-2xl font-semibold text-[var(--ax-fg)]">육성리더 코칭</h2>
        <p className="text-[var(--ax-fg)]/70">상세 내용 준비중입니다.</p>
      </div>
    </PageLayout>
  )
}

export default function LeaderCoachingPage() {
  return (
    <ProtectedRoute>
      <LeaderCoachingContent />
    </ProtectedRoute>
  )
}
