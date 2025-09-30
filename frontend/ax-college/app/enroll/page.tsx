import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"
import Link from "next/link"
import { Calendar, BookOpen, ExternalLink, Building, Clock } from "lucide-react"

export default function EnrollPage() {
  const enrollmentOptions = [
    {
      title: "연간 학습 계획 수립",
      description: "체계적인 연간 학습 로드맵 작성",
      icon: Calendar,
      href: "/enroll/plan",
    },
    {
      title: "교육 프로그램",
      description: "다양한 교육 프로그램 안내",
      icon: BookOpen,
      href: "/enroll/programs",
    },
    {
      title: "외부 미등록 과정",
      description: "외부 교육기관 과정 신청",
      icon: ExternalLink,
      href: "/enroll/external-unlisted",
    },
    {
      title: "사내 자체 과정",
      description: "사내에서 진행하는 교육과정",
      icon: Building,
      href: "/enroll/internal",
    },
    {
      title: "월별 사내과정 일정",
      description: "월별 사내 교육 일정 확인",
      icon: Clock,
      href: "/enroll/internal-monthly",
    },
  ]

  return (
    <PageLayout>
      <PageHeader title="수강신청" description="다양한 교육과정에 수강신청하고 학습 계획을 세워보세요." />

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {enrollmentOptions.map((option) => {
          const Icon = option.icon
          return (
            <Link
              key={option.href}
              href={option.href}
              className="ax-card ax-focus-ring group p-6 transition-all duration-200 hover:shadow-lg"
            >
              <div className="mb-4 flex items-center gap-3">
                <div className="rounded-lg bg-[var(--ax-accent)]/10 p-2 transition-colors group-hover:bg-[var(--ax-accent)]/20">
                  <Icon className="h-6 w-6 text-[var(--ax-accent)]" />
                </div>
              </div>
              <h3 className="mb-2 text-lg font-semibold text-[var(--ax-fg)] group-hover:text-[var(--ax-accent)]">
                {option.title}
              </h3>
              <p className="text-pretty text-sm text-[var(--ax-fg)]/70">{option.description}</p>
            </Link>
          )
        })}
      </div>
    </PageLayout>
  )
}
