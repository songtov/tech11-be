import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"
import Link from "next/link"
import { BookOpen, GraduationCap } from "lucide-react"

export default function GuidePage() {
  const guides = [
    {
      title: "Learning Guide",
      description: "효과적인 학습 방법과 가이드라인",
      icon: BookOpen,
      href: "/guide",
      current: true,
    },
    {
      title: "학사관리 Guide",
      description: "학사 관리 시스템 이용 안내",
      icon: GraduationCap,
      href: "/guide/academic",
      current: false,
    },
  ]

  return (
    <PageLayout>
      <PageHeader title="Learning Guide" description="효과적인 학습을 위한 가이드와 팁을 제공합니다." />

      <div className="grid gap-6 md:grid-cols-2">
        {guides.map((guide) => {
          const Icon = guide.icon
          return (
            <div key={guide.href} className="ax-card p-6">
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-lg bg-[var(--ax-accent)]/10 p-2">
                  <Icon className="h-6 w-6 text-[var(--ax-accent)]" />
                </div>
                <h3 className="text-xl font-semibold text-[var(--ax-fg)]">{guide.title}</h3>
              </div>
              <p className="mb-4 text-pretty text-[var(--ax-fg)]/70">{guide.description}</p>
              {!guide.current && (
                <Link
                  href={guide.href}
                  className="ax-button-primary ax-focus-ring inline-flex items-center px-4 py-2 text-sm font-medium"
                >
                  자세히 보기
                </Link>
              )}
            </div>
          )
        })}
      </div>
    </PageLayout>
  )
}
