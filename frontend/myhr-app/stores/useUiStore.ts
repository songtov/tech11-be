"use client"

import { create } from "zustand"
import { persist } from "zustand/middleware"

interface RecentPage {
  id: string
  title: string
  path: string
  visitedAt: string
}

interface RecentClosedTab {
  id: string
  title: string
  path: string
  closedAt: string
}

interface UiState {
  // Sidebar state
  expandedSections: string[]
  activeMenuId: string

  // Recent pages and closed tabs
  recentVisited: RecentPage[]
  recentClosed: RecentClosedTab[]

  // Actions
  toggleSection: (sectionId: string) => void
  setActiveMenu: (menuId: string) => void
  addRecentPage: (page: Omit<RecentPage, "id" | "visitedAt">) => void
  addClosedTab: (tab: Omit<RecentClosedTab, "id" | "closedAt">) => void
  reopenClosedTab: (tabId: string) => string | null
}

export const useUiStore = create<UiState>()(
  persist(
    (set, get) => ({
      // Initial state
      expandedSections: ["performance"],
      activeMenuId: "performance-dashboard",
      recentVisited: [
        { id: "1", title: "성과 대시보드", path: "/performance", visitedAt: "2024-03-15T10:30:00Z" },
        { id: "2", title: "목표 관리", path: "/performance/goals", visitedAt: "2024-03-15T09:15:00Z" },
      ],
      recentClosed: [
        { id: "1", title: "목표 상세", path: "/performance/goals/1", closedAt: "2024-03-15T11:00:00Z" },
        { id: "2", title: "평가 작성", path: "/performance/reviews/1", closedAt: "2024-03-15T10:45:00Z" },
        { id: "3", title: "피드백 목록", path: "/performance/feedback", closedAt: "2024-03-15T10:30:00Z" },
      ],

      // Actions
      toggleSection: (sectionId: string) => {
        set((state) => ({
          expandedSections: state.expandedSections.includes(sectionId)
            ? state.expandedSections.filter((id) => id !== sectionId)
            : [...state.expandedSections, sectionId],
        }))
      },

      setActiveMenu: (menuId: string) => {
        set({ activeMenuId: menuId })
      },

      addRecentPage: (page) => {
        set((state) => {
          const newPage: RecentPage = {
            ...page,
            id: Date.now().toString(),
            visitedAt: new Date().toISOString(),
          }

          // Remove duplicate if exists
          const filtered = state.recentVisited.filter((p) => p.path !== page.path)

          // Add to front and limit to 20 items
          const updated = [newPage, ...filtered].slice(0, 20)

          return { recentVisited: updated }
        })
      },

      addClosedTab: (tab) => {
        set((state) => {
          const newTab: RecentClosedTab = {
            ...tab,
            id: Date.now().toString(),
            closedAt: new Date().toISOString(),
          }

          // Add to front and limit to 10 items
          const updated = [newTab, ...state.recentClosed].slice(0, 10)

          return { recentClosed: updated }
        })
      },

      reopenClosedTab: (tabId: string) => {
        const { recentClosed } = get()
        const tab = recentClosed.find((t) => t.id === tabId)

        if (tab) {
          // Add to recent visited
          get().addRecentPage({ title: tab.title, path: tab.path })

          // Remove from closed tabs
          set((state) => ({
            recentClosed: state.recentClosed.filter((t) => t.id !== tabId),
          }))

          // Navigate to the tab (this would be handled by the component)
          return tab.path
        }

        return null
      },
    }),
    {
      name: "myhr-ui-store",
      partialize: (state) => ({
        expandedSections: state.expandedSections,
        activeMenuId: state.activeMenuId,
        recentVisited: state.recentVisited,
        recentClosed: state.recentClosed,
      }),
    },
  ),
)
