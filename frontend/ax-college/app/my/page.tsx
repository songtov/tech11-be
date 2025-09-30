"use client"

import { ProtectedRoute } from "@/components/Auth/ProtectedRoute"
import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"
import { useAuth } from "@/hooks/use-auth"
import Link from "next/link"
import { User, BookOpen, Award, Globe, FileText, Users, TrendingUp } from "lucide-react"

function MyPageContent() {
  const { user } = useAuth()

  const myPageSections = [
    {
      title: "나의 학사 현황",
      description: "전체적인 학습 현황을 확인하세요",
      icon: TrendingUp,
      href: "/my/overview",
    },
    {
      title: "Learning History",
      description: "지금까지의 학습 이력을 확인하세요",
      icon: BookOpen,
      href: "/my/history",
    },
    {
      title: "Learning Account",
      description: "학습 계정 정보를 관리하세요",
      icon: User,
      href: "/my/account",
    },
    {
      title: "전문가 활동",
      description: "전문가 활동 내역을 확인하세요",
      icon: Users,
      href: "/my/expert",
    },
    {
      title: "외국어",
      description: "외국어 학습 현황을 관리하세요",
      icon: Globe,
      href: "/my/language",
    },
    {
      title: "자격증",
      description: "취득한 자격증을 관리하세요",
      icon: Award,
      href: "/my/certificates",
    },
    {
      title: "육성리더 코칭",
      description: "리더십 코칭 프로그램 현황",
      icon: FileText,
      href: "/my/leader-coaching",
    },
  ]

  return (
    <PageLayout>
      <PageHeader title={`${user?.name}님의 학사 현황`} description="개인 학습 정보와 현황을 한눈에 확인하세요." />

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {myPageSections.map((section) => {
          const Icon = section.icon
          return (
            <Link
              key={section.href}
              href={section.href}
              className="ax-card ax-focus-ring group p-6 transition-all duration-200 hover:shadow-lg"
            >
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-lg bg-[var(--ax-accent)]/10 p-2 transition-colors group-hover:bg-[var(--ax-accent)]/20">
                  <Icon className="h-6 w-6 text-[var(--ax-accent)]" />
                </div>
              </div>
              <h3 className="mb-2 text-lg font-semibold text-[var(--ax-fg)] group-hover:text-[var(--ax-accent)]">
                {section.title}
              </h3>
              <p className="text-pretty text-sm text-[var(--ax-fg)]/70">{section.description}</p>
            </Link>
          )
        })}
      </div>
    </PageLayout>
  )
}

export default function MyPage() {
  return (
    <ProtectedRoute>
      <MyPageContent />
    </ProtectedRoute>
  )
}
