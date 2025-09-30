"use client"

import { ProtectedRoute } from "@/components/Auth/ProtectedRoute"
import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"

function LanguageContent() {
  return (
    <PageLayout>
      <PageHeader title="외국어" description="외국어 학습 현황을 관리하세요." />

      <div className="ax-card p-8 text-center">
        <h2 className="mb-4 text-2xl font-semibold text-[var(--ax-fg)]">외국어 학습</h2>
        <p className="text-[var(--ax-fg)]/70">상세 내용 준비중입니다.</p>
      </div>
    </PageLayout>
  )
}

export default function LanguagePage() {
  return (
    <ProtectedRoute>
      <LanguageContent />
    </ProtectedRoute>
  )
}
