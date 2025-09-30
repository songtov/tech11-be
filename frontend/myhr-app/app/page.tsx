"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"

export default function HomePage() {
  const router = useRouter()

  useEffect(() => {
    // Redirect to performance dashboard as specified
    router.replace("/performance")
  }, [router])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h1 className="text-2xl font-semibold text-foreground mb-2">MyHR</h1>
        <p className="text-muted-foreground">리다이렉트 중...</p>
      </div>
    </div>
  )
}
