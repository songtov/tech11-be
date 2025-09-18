"use client"

import { useEffect } from "react"
import { PageLayout } from "@/components/Layout/PageLayout"
import { EmptyState } from "@/components/UI/EmptyState"

export default function Error({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => {
    console.error("Global error:", error)
  }, [error])

  return (
    <PageLayout>
      <EmptyState
        title="오류가 발생했습니다"
        description="페이지를 불러오는 중 문제가 발생했습니다."
        action={{ label: "다시 시도", href: "#" }}
      />
      <div className="mt-4 text-center">
        <button type="button" onClick={reset} className="ax-button-primary ax-focus-ring px-4 py-2 text-sm font-medium">
          다시 시도
        </button>
      </div>
    </PageLayout>
  )
}
