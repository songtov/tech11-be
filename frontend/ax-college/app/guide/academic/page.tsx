import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"

export default function AcademicGuidePage() {
  return (
    <PageLayout>
      <PageHeader title="학사관리 Guide" description="학사 관리 시스템 이용 방법을 안내합니다." />

      <div className="ax-card p-8 text-center">
        <h2 className="mb-4 text-2xl font-semibold text-[var(--ax-fg)]">학사관리 Guide</h2>
        <p className="text-[var(--ax-fg)]/70">상세 내용 준비중입니다.</p>
      </div>
    </PageLayout>
  )
}
