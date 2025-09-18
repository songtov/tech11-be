import { PageLayout } from "@/components/Layout/PageLayout"
import { PageHeader } from "@/components/UI/PageHeader"
import Link from "next/link"
import { ArrowRight } from "lucide-react"

export default function CurriculumPage() {
  const curriculumTypes = [
    {
      title: "학부별 교육체계",
      description: "각 학부별 특성에 맞는 전문 교육과정",
      href: "/curriculum/department",
    },
    {
      title: "사업별 교육체계",
      description: "사업 영역별 맞춤형 교육 프로그램",
      href: "/curriculum/business",
    },
  ]

  return (
    <PageLayout>
      <PageHeader title="교육체계" description="체계적이고 전문적인 교육과정을 제공합니다." />

      <div className="grid gap-6 md:grid-cols-2">
        {curriculumTypes.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className="ax-card ax-focus-ring group p-6 transition-all duration-200 hover:shadow-lg"
          >
            <div className="flex items-center justify-between">
              <div>
                <h3 className="mb-2 text-xl font-semibold text-[var(--ax-fg)] group-hover:text-[var(--ax-accent)]">
                  {item.title}
                </h3>
                <p className="text-pretty text-[var(--ax-fg)]/70">{item.description}</p>
              </div>
              <ArrowRight className="h-5 w-5 text-[var(--ax-accent)] transition-transform group-hover:translate-x-1" />
            </div>
          </Link>
        ))}
      </div>
    </PageLayout>
  )
}
