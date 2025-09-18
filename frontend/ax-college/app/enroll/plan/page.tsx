import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"

export default function EnrollPlanPage() {
  return (
    <PageLayout>
      <PageHeader title="연간 학습 계획 수립" description="체계적인 연간 학습 로드맵을 작성해보세요." />

      <div className="ax-card p-8 text-center">
        <h2 className="mb-4 text-2xl font-semibold text-[var(--ax-fg)]">연간 학습 계획 수립</h2>
        <p className="text-[var(--ax-fg)]/70">상세 내용 준비중입니다.</p>
      </div>
    </PageLayout>
  )
}
