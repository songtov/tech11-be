"use client"

import {
  Star,
  Briefcase,
  UserRound,
  Megaphone,
  Coins,
  CalendarClock,
  HeartHandshake,
  TrendingUp,
  Globe,
  Headphones,
  GraduationCap,
  CircleArrowLeftIcon,
  CircleDashed,
  Trello,
} from "lucide-react"
import SidebarSection from "./SidebarSection"
import type { MenuItem } from "./types"
import PinnedRecentClosedTabs from "./PinnedRecentClosedTabs"
import { useUiStore } from "@/stores/useUiStore"

// moved to types.ts

const menuItems: MenuItem[] = [
  { id: "favorites", label: "즐겨찾기", icon: Star, path: "/favorites" },
  { id: "tasks", label: "업무 담당", icon: Briefcase, path: "/tasks" },
  { id: "profile", label: "Profile", icon: UserRound, path: "/profile" },
  { id: "internal-apply", label: "사내 공모", icon: Megaphone, path: "/internal-apply" },
  { id: "rewards", label: "보상", icon: Coins, path: "/rewards" },
  { id: "attendance", label: "근태", icon: CalendarClock, path: "/attendance" },
  { id: "welfare", label: "복리후생", icon: HeartHandshake, path: "/welfare" },
  {
    id: "performance",
    label: "성과관리",
    icon: TrendingUp,
    children: [
      { id: "performance-dashboard", label: "대시보드", icon: TrendingUp, path: "/performance" },
      { id: "performance-goals", label: "목표", icon: TrendingUp, path: "/performance/goals" },
      {
        id: "reviews-group",
        label: "평가",
        icon: Trello,
        children: [
          { id: "performance-reviews", label: "나의 평가", icon: TrendingUp, path: "/performance/reviews" },
          { id: "performance-feedback", label: "동료/ 중간 평가", icon: TrendingUp, path: "/performance/feedback" },
          { id: "performance-calibration", label: "평가 이력", icon: TrendingUp, path: "/performance/calibration" },
        ],
      },
      {
        id: "360-review",
        label: "360° Review",
        icon: CircleDashed,
        children: [
          { id: "performance-midleader", label: "중간 리더 본인 결과 조회", icon: TrendingUp, path: "/performance/360/midleader" },
        ],
      },
    ],
  },
  { id: "global", label: "Global", icon: Globe, path: "/global" },
  { id: "hr-service", label: "HR서비스", icon: Headphones, path: "/hr-service" },
  { id: "college", label: "College", icon: GraduationCap, path: "http://localhost:3001" },
]

export default function LeftSidebar() {
  const { expandedSections, activeMenuId, toggleSection, setActiveMenu } = useUiStore()

  return (
    <aside className="w-[280px] bg-[var(--sidebar-bg)] text-[var(--sidebar-fg)] flex flex-col h-screen">
      <div className="flex-1 overflow-y-auto py-4">
        {menuItems.map((item) => (
          <SidebarSection
            key={item.id}
            item={item}
            expandedSections={expandedSections}
            activeId={activeMenuId}
            onToggle={toggleSection}
            onSetActive={setActiveMenu}
            level={0}
          />
        ))}
      </div>

      <PinnedRecentClosedTabs />
    </aside>
  )
}
