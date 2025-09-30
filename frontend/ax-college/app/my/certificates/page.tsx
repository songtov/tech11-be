"use client"

import { ProtectedRoute } from "@/components/Auth/ProtectedRoute"
import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"

function CertificatesContent() {
  return (
    <PageLayout>
      <PageHeader title="자격증" description="취득한 자격증을 관리하세요." />

      <div className="ax-card p-8 text-center">
        <h2 className="mb-4 text-2xl font-semibold text-[var(--ax-fg)]">자격증 관리</h2>
        <p className="text-[var(--ax-fg)]/70">상세 내용 준비중입니다.</p>
      </div>
    </PageLayout>
  )
}

export default function CertificatesPage() {
  return (
    <ProtectedRoute>
      <CertificatesContent />
    </ProtectedRoute>
  )
}
