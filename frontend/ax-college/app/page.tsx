import { Header } from "@/components/Header/Header"
import Link from "next/link"
import { ArrowRight, BookOpen, Users, Calendar, TrendingUp } from "lucide-react"

export default function HomePage() {
  const quickLinks = [
    {
      title: "수강신청",
      description: "새로운 교육과정에 신청하세요",
      href: "/enroll",
      icon: Calendar,
      color: "bg-blue-500",
    },
    {
      title: "Learning Guide",
      description: "효과적인 학습 방법을 확인하세요",
      href: "/guide",
      icon: BookOpen,
      color: "bg-green-500",
    },
    {
      title: "AXpress",
      description: "최신 뉴스와 정보를 확인하세요",
      href: "/axpress",
      icon: TrendingUp,
      color: "bg-purple-500",
    },
    {
      title: "My Page",
      description: "나의 학습 현황을 확인하세요",
      href: "/my",
      icon: Users,
      color: "bg-orange-500",
    },
  ]

  const recentNews = [
    {
      title: "2024년 새로운 교육과정 출시",
      date: "2024-01-15",
      category: "뉴스",
    },
    {
      title: "수강신청 일정 안내",
      date: "2024-01-10",
      category: "공지",
    },
    {
      title: "온라인 세미나 개최",
      date: "2024-01-08",
      category: "이벤트",
    },
  ]

  return (
    <div className="min-h-screen">
      <Header />
      <main>
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-[var(--ax-bg-soft)] to-white py-12 md:py-16 lg:py-24">
          <div className="mx-auto max-w-7xl px-4 md:px-6 lg:px-8">
            <div className="text-center">
              <h1 className="mb-4 text-balance text-3xl font-bold text-[var(--ax-fg)] md:mb-6 md:text-4xl lg:text-5xl xl:text-6xl">
                AX College에 오신 것을 환영합니다
              </h1>
              <p className="mx-auto mb-6 max-w-2xl text-pretty text-base text-[var(--ax-fg)]/80 md:mb-8 md:text-lg lg:text-xl">
                체계적인 교육과정과 개인 맞춤형 학습 관리를 통해 전문성을 키워나가세요. AX College에서 새로운 학습
                경험을 시작하세요.
              </p>
              <div className="flex flex-col gap-3 sm:flex-row sm:justify-center sm:gap-4">
                <Link
                  href="/enroll"
                  className="ax-button-primary ax-focus-ring inline-flex items-center justify-center gap-2 px-6 py-3 text-sm font-medium md:text-base"
                >
                  수강신청 시작하기
                  <ArrowRight className="h-4 w-4 md:h-5 md:w-5" />
                </Link>
                <Link
                  href="/about"
                  className="ax-focus-ring inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--ax-border)] bg-[var(--ax-surface)] px-6 py-3 text-sm font-medium text-[var(--ax-fg)] transition-colors hover:bg-[var(--ax-border)] md:text-base"
                >
                  College 소개
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Quick Links */}
        <section className="py-12 md:py-16">
          <div className="mx-auto max-w-7xl px-4 md:px-6 lg:px-8">
            <div className="mb-8 text-center md:mb-12">
              <h2 className="mb-3 text-2xl font-bold text-[var(--ax-fg)] md:mb-4 md:text-3xl">빠른 메뉴</h2>
              <p className="text-base text-[var(--ax-fg)]/70 md:text-lg">자주 사용하는 기능에 빠르게 접근하세요</p>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4 lg:gap-6">
              {quickLinks.map((link) => {
                const Icon = link.icon
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    className="ax-card ax-focus-ring group p-4 transition-all duration-200 hover:shadow-lg md:p-6"
                  >
                    <div className="mb-3 md:mb-4">
                      <div className={`inline-flex rounded-lg p-2 md:p-3 ${link.color} text-white`}>
                        <Icon className="h-5 w-5 md:h-6 md:w-6" />
                      </div>
                    </div>
                    <h3 className="mb-2 text-base font-semibold text-[var(--ax-fg)] group-hover:text-[var(--ax-accent)] md:text-lg">
                      {link.title}
                    </h3>
                    <p className="text-pretty text-sm text-[var(--ax-fg)]/70">{link.description}</p>
                  </Link>
                )
              })}
            </div>
          </div>
        </section>

        {/* Recent News */}
        <section className="bg-[var(--ax-surface)] py-12 md:py-16">
          <div className="mx-auto max-w-7xl px-4 md:px-6 lg:px-8">
            <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between md:mb-12">
              <div>
                <h2 className="mb-2 text-2xl font-bold text-[var(--ax-fg)] md:text-3xl">최근 소식</h2>
                <p className="text-base text-[var(--ax-fg)]/70 md:text-lg">AX College의 최신 뉴스와 공지사항</p>
              </div>
              <Link
                href="/axpress"
                className="ax-focus-ring inline-flex items-center gap-2 text-sm text-[var(--ax-accent)] hover:underline md:text-base"
              >
                전체 보기
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 lg:gap-6">
              {recentNews.map((news, index) => (
                <div key={index} className="ax-card p-4 md:p-6">
                  <div className="mb-3 flex items-center justify-between">
                    <span className="rounded-full bg-[var(--ax-accent)]/10 px-2 py-1 text-xs font-medium text-[var(--ax-accent)] md:px-3">
                      {news.category}
                    </span>
                    <span className="text-xs text-[var(--ax-fg)]/60">{news.date}</span>
                  </div>
                  <h3 className="text-base font-semibold text-[var(--ax-fg)] md:text-lg">{news.title}</h3>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="py-12 md:py-16">
          <div className="mx-auto max-w-7xl px-4 md:px-6 lg:px-8">
            <div className="mb-8 text-center md:mb-12">
              <h2 className="mb-3 text-2xl font-bold text-[var(--ax-fg)] md:mb-4 md:text-3xl">AX College 특징</h2>
              <p className="text-base text-[var(--ax-fg)]/70 md:text-lg">체계적이고 전문적인 교육 환경을 제공합니다</p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 lg:gap-8">
              <div className="text-center">
                <div className="mb-3 inline-flex rounded-full bg-[var(--ax-accent)]/10 p-3 md:mb-4 md:p-4">
                  <BookOpen className="h-6 w-6 text-[var(--ax-accent)] md:h-8 md:w-8" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-[var(--ax-fg)] md:text-xl">체계적인 교육과정</h3>
                <p className="text-pretty text-sm text-[var(--ax-fg)]/70 md:text-base">
                  학부별, 사업별로 특화된 교육과정을 통해 전문성을 키울 수 있습니다.
                </p>
              </div>

              <div className="text-center">
                <div className="mb-3 inline-flex rounded-full bg-[var(--ax-accent)]/10 p-3 md:mb-4 md:p-4">
                  <Users className="h-6 w-6 text-[var(--ax-accent)] md:h-8 md:w-8" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-[var(--ax-fg)] md:text-xl">개인 맞춤 관리</h3>
                <p className="text-pretty text-sm text-[var(--ax-fg)]/70 md:text-base">
                  개인별 학습 현황과 진도를 체계적으로 관리하고 추적할 수 있습니다.
                </p>
              </div>

              <div className="text-center">
                <div className="mb-3 inline-flex rounded-full bg-[var(--ax-accent)]/10 p-3 md:mb-4 md:p-4">
                  <TrendingUp className="h-6 w-6 text-[var(--ax-accent)] md:h-8 md:w-8" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-[var(--ax-fg)] md:text-xl">지속적인 성장</h3>
                <p className="text-pretty text-sm text-[var(--ax-fg)]/70 md:text-base">
                  최신 트렌드와 연구 자료를 통해 지속적인 학습과 성장을 지원합니다.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--ax-border)] bg-[var(--ax-surface)] py-8 md:py-12">
        <div className="mx-auto max-w-7xl px-4 md:px-6 lg:px-8">
          <div className="text-center">
            <h3 className="mb-3 text-xl font-bold text-[var(--ax-fg)] md:mb-4 md:text-2xl">AX College</h3>
            <p className="mb-4 text-sm text-[var(--ax-fg)]/70 md:mb-6 md:text-base">
              체계적인 교육과 개인 맞춤형 학습 관리 시스템
            </p>
            <div className="flex flex-wrap justify-center gap-4 text-xs text-[var(--ax-fg)]/60 md:gap-6 md:text-sm">
              <Link href="/about" className="hover:text-[var(--ax-accent)]">
                College 소개
              </Link>
              <Link href="/curriculum" className="hover:text-[var(--ax-accent)]">
                교육체계
              </Link>
              <Link href="/guide" className="hover:text-[var(--ax-accent)]">
                Learning Guide
              </Link>
              <Link href="/enroll" className="hover:text-[var(--ax-accent)]">
                수강신청
              </Link>
              <Link href="/axpress" className="hover:text-[var(--ax-accent)]">
                AXpress
              </Link>
            </div>
            <div className="mt-6 border-t border-[var(--ax-border)] pt-6 text-xs text-[var(--ax-fg)]/50 md:mt-8 md:pt-8">
              © 2024 AX College. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
