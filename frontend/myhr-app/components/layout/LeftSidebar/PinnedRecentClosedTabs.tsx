"use client"

import { History } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useUiStore } from "@/stores/useUiStore"
import { useRouter } from "next/navigation"

export default function PinnedRecentClosedTabs() {
  const { recentClosed, reopenClosedTab } = useUiStore()
  const router = useRouter()

  const handleReopenTab = (tabId: string) => {
    const path = reopenClosedTab(tabId)
    if (path) {
      router.push(path)
    }
  }

  return (
    <div className="border-t border-white/10 p-4">
      <div className="flex items-center gap-2 mb-3">
        <History className="h-4 w-4 opacity-60" />
        <span className="text-sm opacity-80">최근 닫은 탭</span>
      </div>

      <div className="space-y-1">
        {recentClosed.slice(0, 5).map((tab) => (
          <Button
            key={tab.id}
            variant="ghost"
            size="sm"
            className="w-full justify-start px-2 py-1 h-auto text-xs text-[var(--sidebar-fg)]/70 hover:bg-white/10"
            onClick={() => handleReopenTab(tab.id)}
          >
            {tab.title}
          </Button>
        ))}

        {recentClosed.length === 0 && (
          <p className="text-xs text-[var(--sidebar-fg)]/50 px-2">최근 닫은 탭이 없습니다</p>
        )}
      </div>
    </div>
  )
}
