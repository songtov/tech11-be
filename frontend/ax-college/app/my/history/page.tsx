"use client"

import { ProtectedRoute } from "@/components/Auth/ProtectedRoute"
import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"

function HistoryContent() {
  return (
    <PageLayout>
      <PageHeader title="Learning History" description="지금까지의 학습 이력을 확인하세요." />

      <div className="ax-card p-8 text-center">
        <h2 className="mb-4 text-2xl font-semibold text-[var(--ax-fg)]">학습 이력</h2>
        <p className="text-[var(--ax-fg)]/70">상세 내용 준비중입니다.</p>
      </div>
    </PageLayout>
  )
}

export default function HistoryPage() {
  return (
    <ProtectedRoute>
      <HistoryContent />
    </ProtectedRoute>
  )
}
