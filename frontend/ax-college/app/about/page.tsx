import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"

export default function AboutPage() {
  return (
    <PageLayout>
      <PageHeader title="College 소개" description="AX College의 교육 철학과 비전을 소개합니다." />

      <div className="grid gap-8 lg:grid-cols-2">
        <div className="ax-card p-6">
          <h2 className="mb-4 text-2xl font-semibold text-[var(--ax-fg)]">교육 철학</h2>
          <p className="text-pretty leading-relaxed text-[var(--ax-fg)]/80">
            AX College는 실무 중심의 교육을 통해 전문성을 갖춘 인재를 양성하는 것을 목표로 합니다. 체계적인 교육과정과
            실무 경험을 바탕으로 한 학습 환경을 제공합니다.
          </p>
        </div>

        <div className="ax-card p-6">
          <h2 className="mb-4 text-2xl font-semibold text-[var(--ax-fg)]">비전</h2>
          <p className="text-pretty leading-relaxed text-[var(--ax-fg)]/80">
            미래 지향적 교육 시스템을 통해 변화하는 시대에 적응할 수 있는 창의적이고 전문적인 인재를 육성하여 사회
            발전에 기여합니다.
          </p>
        </div>
      </div>
    </PageLayout>
  )
}
