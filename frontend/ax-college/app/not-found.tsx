import { PageLayout } from "@/components/Layout/PageLayout"
import { EmptyState } from "@/components/UI/EmptyState"

export default function NotFound() {
  return (
    <PageLayout>
      <EmptyState
        title="페이지를 찾을 수 없습니다"
        description="요청하신 페이지가 존재하지 않거나 이동되었습니다."
        action={{ label: "홈으로", href: "/" }}
      />
    </PageLayout>
  )
}
