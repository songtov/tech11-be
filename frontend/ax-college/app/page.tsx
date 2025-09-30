import { Header } from "@/components/Header/Header"
import Link from "next/link"
import { ArrowRight, BookOpen, Users, Calendar, TrendingUp } from "lucide-react"

export default function HomePage() {
  const quickLinks = [
    {
      title: "수강신청",
      description: "AXpress와 연계된 과정에 바로 신청하세요",
      href: "/enroll",
      icon: Calendar,
      color: "bg-blue-500",
    },
    {
      title: "AXpress 가이드",
      description: "신기술 학습 부담을 줄이는 사용 TIP을 확인하세요",
      href: "/guide",
      icon: BookOpen,
      color: "bg-green-500",
    },
    {
      title: "AXpress",
      description: "6개 도메인×각 5편 최신 논문을 MyHR와 연동해 한 번에",
      href: "/axpress",
      icon: TrendingUp,
      color: "bg-purple-500",
    },
    {
      title: "My Page",
      description: "퀴즈 성과·커뮤니티 아카이빙·MyHR 자동기록을 확인하세요",
      href: "/my",
      icon: Users,
      color: "bg-orange-500",
    },
  ]

  const recentNews = [
    {
      title: "AXpress 베타 오픈: 6개 도메인 최신 논문 30편 자동 큐레이션",
      date: "2025-09-18",
      category: "뉴스",
    },
    {
      title: "퀴즈로 핵심만 학습: 한글 요약·복습 카드팩 출시",
      date: "2025-09-10",
      category: "업데이트",
    },
    {
      title: "MyHR 교육이력 자동 반영 시작 (AXpress 학습 활동 포함)",
      date: "2025-09-03",
      category: "공지",
    },
  ]

  return (
    <div className="min-h-screen">
      <Header />
      <main>
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-[var(--ax-bg-soft)] to-white py-12 md:py-16 lg:py-54">
          <div className="mx-auto max-w-7xl px-4 md:px-6 lg:px-8">
            <div className="text-center">
              <h1 className="mb-4 text-balance text-3xl font-bold text-[var(--ax-fg)] md:mb-6 md:text-4xl lg:text-5xl xl:text-6xl">
                신기술 학습 부담을 덜어주는 플랫폼, AXpress
              </h1>
              <p className="mx-auto mb-6 max-w-2xl text-pretty text-base text-[var(--ax-fg)]/80 md:mb-8 md:text-lg lg:text-xl">
                6개 도메인 최신 논문을 MyHR와 연동해 모아 보고, 한글 퀴즈로 핵심을 빠르게 학습하고,
                커뮤니티에 내 학습을 아카이빙하세요. 학습 결과는 MyHR 교육이력에 자동 기록됩니다.
              </p>
              <div className="flex flex-col gap-3 sm:flex-row sm:justify-center sm:gap-4">
                <Link
                  href="/enroll"
                  className="ax-button-primary ax-focus-ring inline-flex items-center justify-center gap-2 px-6 py-3 text-sm font-medium md:text-base"
                >
                  지금 시작하기
                  <ArrowRight className="h-4 w-4 md:h-5 md:w-5" />
                </Link>
                <Link
                  href="/about"
                  className="ax-focus-ring inline-flex items-center justify-center gap-2 rounded-lg border border-[var(--ax-border)] bg-[var(--ax-surface)] px-6 py-3 text-sm font-medium text-[var(--ax-fg)] transition-colors hover:bg-[var(--ax-border)] md:text-base"
                >
                  AXpress 소개
                </Link>
              </div>
            </div>
          </div>
        </section>

        {/* Quick Links */}
        <section className="bg-gradient-to-br from-[var(--ax-bg-soft)] to-white py-12 md:py-16 lg:py-54">
          <div className="mx-auto max-w-7xl px-4 md:px-6 lg:px-8">
            <div className="mb-8 text-center md:mb-12">
              <h2 className="mb-3 text-2xl font-bold text-[var(--ax-fg)] md:mb-4 md:text-3xl">빠른 메뉴</h2>
              <p className="text-base text-[var(--ax-fg)]/70 md:text-lg">AXpress 핵심 기능으로 바로 이동하세요</p>
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
        <section className="bg-[var(--ax-surface)] py-12 md:py-16 lg:py-54">
          <div className="mx-auto max-w-7xl px-4 md:px-6 lg:px-8">
            <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between md:mb-12">
              <div>
                <h2 className="mb-2 text-2xl font-bold text-[var(--ax-fg)] md:text-3xl">최근 소식</h2>
                <p className="text-base text-[var(--ax-fg)]/70 md:text-lg">AXpress 업데이트와 연동 공지</p>
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
        <section className="py-12 md:py-16 lg:py-54">
          <div className="mx-auto max-w-7xl px-4 md:px-6 lg:px-8">
            <div className="mb-8 text-center md:mb-12">
              <h2 className="mb-3 text-2xl font-bold text-[var(--ax-fg)] md:mb-4 md:text-3xl">AXpress 핵심 기능</h2>
              <p className="text-base text-[var(--ax-fg)]/70 md:text-lg">
                “읽기-이해-기록”을 한 곳에서, MyHR와 매끄럽게 연동합니다
              </p>
            </div>

            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3 lg:gap-8">
              <div className="text-center">
                <div className="mb-3 inline-flex rounded-full bg-[var(--ax-accent)]/10 p-3 md:mb-4 md:p-4">
                  <BookOpen className="h-6 w-6 text-[var(--ax-accent)] md:h-8 md:w-8" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-[var(--ax-fg)] md:text-xl">최신 논문 큐레이션</h3>
                <p className="text-pretty text-sm text-[var(--ax-fg)]/70 md:text-base">
                  6개 도메인별 최신 5편(총 30편)을 자동 선별해 MyHR와 연동된 한 화면에서 빠르게 탐색합니다.
                </p>
              </div>

              <div className="text-center">
                <div className="mb-3 inline-flex rounded-full bg-[var(--ax-accent)]/10 p-3 md:mb-4 md:p-4">
                  <Users className="h-6 w-6 text-[var(--ax-accent)] md:h-8 md:w-8" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-[var(--ax-fg)] md:text-xl">퀴즈 기반 핵심 학습</h3>
                <p className="text-pretty text-sm text-[var(--ax-fg)]/70 md:text-base">
                  논문의 핵심을 한글 퀴즈로 즉시 복습하고 이해도를 확인해 개인 맞춤형 학습 부담을 줄여줍니다.
                </p>
              </div>

              <div className="text-center">
                <div className="mb-3 inline-flex rounded-full bg-[var(--ax-accent)]/10 p-3 md:mb-4 md:p-4">
                  <TrendingUp className="h-6 w-6 text-[var(--ax-accent)] md:h-8 md:w-8" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-[var(--ax-fg)] md:text-xl">아카이빙 & MyHR 자동기록</h3>
                <p className="text-pretty text-sm text-[var(--ax-fg)]/70 md:text-base">
                  커뮤니티에 학습 노트를 아카이빙하고, 활동 내역은 MyHR 교육이력에 자동 반영되어 혁신 학습 기록을 남깁니다.
                </p>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--ax-border)] bg-[var(--ax-surface)] py-12 md:py-16 lg:py-54">
        <div className="mx-auto max-w-7xl px-4 md:px-6 lg:px-8">
          <div className="text-center">           
            <div className="flex flex-wrap justify-center gap-4 text-xs text-[var(--ax-fg)]/60 md:gap-6 md:text-sm">
              <Link href="/about" className="hover:text-[var(--ax-accent)]">
                College 소개
              </Link>
              <Link href="/curriculum" className="hover:text-[var(--ax-accent)]">
                교육체계
              </Link>
              <Link href="/guide" className="hover:text-[var(--ax-accent)]">
                AXpress 가이드
              </Link>
              <Link href="/enroll" className="hover:text-[var(--ax-accent)]">
                수강신청
              </Link>
              <Link href="/axpress" className="hover:text-[var(--ax-accent)]">
                AXpress
              </Link>
            </div>
            <div className="mt-6 border-t border-[var(--ax-border)] pt-6 text-xs text-[var(--ax-fg)]/50 md:mt-8 md:pt-8">
              © 2025 AX College. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
