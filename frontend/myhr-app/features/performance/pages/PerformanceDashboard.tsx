"use client"

import { TrendingUp, Target, FileText, MessageSquare, Calendar } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import PageContainer from "@/components/layout/PageContainer"
import KPIChart from "../components/KPIChart"
import { Badge } from "@/components/ui/badge"

const kpiData = [
  { month: "1월", goals: 85, reviews: 92, feedback: 78 },
  { month: "2월", goals: 88, reviews: 89, feedback: 82 },
  { month: "3월", goals: 92, reviews: 94, feedback: 85 },
  { month: "4월", goals: 89, reviews: 91, feedback: 88 },
  { month: "5월", goals: 94, reviews: 96, feedback: 91 },
  { month: "6월", goals: 91, reviews: 93, feedback: 89 },
]

const recentItems = [
  {
    id: "1",
    title: "Q2 개인 목표 설정",
    type: "목표",
    status: "진행중",
    updatedAt: "2024-03-15",
    path: "/performance/goals/1",
  },
  {
    id: "2",
    title: "상반기 성과 평가",
    type: "평가",
    status: "미제출",
    updatedAt: "2024-03-14",
    path: "/performance/reviews/1",
  },
  {
    id: "3",
    title: "팀 협업 피드백",
    type: "피드백",
    status: "완료",
    updatedAt: "2024-03-13",
    path: "/performance/feedback",
  },
  {
    id: "4",
    title: "Q1 목표 달성률 검토",
    type: "목표",
    status: "완료",
    updatedAt: "2024-03-12",
    path: "/performance/goals/2",
  },
  {
    id: "5",
    title: "동료 평가 요청",
    type: "평가",
    status: "승인대기",
    updatedAt: "2024-03-11",
    path: "/performance/reviews/2",
  },
]

export default function PerformanceDashboard() {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "완료":
        return "bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/20"
      case "진행중":
        return "bg-[var(--primary)]/10 text-[var(--primary)] border-[var(--primary)]/20"
      case "미제출":
        return "bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/20"
      case "승인대기":
        return "bg-[var(--accent)]/10 text-[var(--accent)] border-[var(--accent)]/20"
      default:
        return "bg-muted text-muted-foreground"
    }
  }

  return (
    <PageContainer title="성과 대시보드">
      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">목표 진행률</CardTitle>
            <Target className="h-4 w-4 text-[var(--primary)]" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-[var(--primary)]">91%</div>
            <p className="text-xs text-muted-foreground">전월 대비 +3%</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">평가 상태</CardTitle>
            <FileText className="h-4 w-4 text-[var(--accent)]" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-[var(--accent)]">진행중</div>
            <p className="text-xs text-muted-foreground">2건 미제출</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">최근 피드백</CardTitle>
            <MessageSquare className="h-4 w-4 text-[var(--success)]" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-[var(--success)]">7건</div>
            <p className="text-xs text-muted-foreground">이번 주 받은 피드백</p>
          </CardContent>
        </Card>
      </div>

      {/* KPI Chart */}
      <Card className="mb-8">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            성과 지표 추이
          </CardTitle>
        </CardHeader>
        <CardContent>
          <KPIChart data={kpiData} />
        </CardContent>
      </Card>

      {/* Recent Items Table */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>최근 활동</CardTitle>
          <Button variant="outline" size="sm">
            전체 보기
          </Button>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentItems.map((item) => (
              <div
                key={item.id}
                className="flex items-center justify-between p-4 border border-border rounded-lg hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    {item.type === "목표" && <Target className="h-4 w-4 text-[var(--primary)]" />}
                    {item.type === "평가" && <FileText className="h-4 w-4 text-[var(--accent)]" />}
                    {item.type === "피드백" && <MessageSquare className="h-4 w-4 text-[var(--success)]" />}
                    <span className="text-sm text-muted-foreground">{item.type}</span>
                  </div>
                  <div>
                    <h4 className="font-medium">{item.title}</h4>
                    <p className="text-sm text-muted-foreground flex items-center gap-2">
                      <Calendar className="h-3 w-3" />
                      {item.updatedAt}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant="outline" className={getStatusColor(item.status)}>
                    {item.status}
                  </Badge>
                  <Button variant="ghost" size="sm">
                    바로가기
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </PageContainer>
  )
}
