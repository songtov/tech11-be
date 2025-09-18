import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"

export default function DepartmentCurriculumPage() {
  return (
    <PageLayout>
      <PageHeader title="학부별 교육체계" description="각 학부의 특성에 맞는 전문 교육과정을 제공합니다." />

      <div className="ax-card p-8 text-center">
        <h2 className="mb-4 text-2xl font-semibold text-[var(--ax-fg)]">학부별 교육체계</h2>
        <p className="text-[var(--ax-fg)]/70">상세 내용 준비중입니다.</p>
      </div>
    </PageLayout>
  )
}
