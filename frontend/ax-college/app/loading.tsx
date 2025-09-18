import { PageLayout } from "@/components/Layout/PageLayout"
import { LoadingSpinner } from "@/components/ui/LoadingSpinner"

export default function Loading() {
  return (
    <PageLayout>
      <div className="flex min-h-[400px] items-center justify-center">
        <div className="ax-card p-8 text-center">
          <LoadingSpinner size="lg" className="mx-auto mb-4" />
          <p className="text-[var(--ax-fg)]/70">페이지를 불러오는 중...</p>
        </div>
      </div>
    </PageLayout>
  )
}
