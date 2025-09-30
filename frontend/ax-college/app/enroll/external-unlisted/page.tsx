import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"

export default function ExternalUnlistedPage() {
  return (
    <PageLayout>
      <PageHeader title="외부 미등록 과정" description="외부 교육기관의 과정을 신청하세요." />

      <div className="ax-card p-8 text-center">
        <h2 className="mb-4 text-2xl font-semibold text-[var(--ax-fg)]">외부 미등록 과정</h2>
        <p className="text-[var(--ax-fg)]/70">상세 내용 준비중입니다.</p>
      </div>
    </PageLayout>
  )
}
