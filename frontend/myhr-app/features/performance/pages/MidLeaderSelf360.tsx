"use client"

import { useState } from "react"
import { TrendingUp, Users, Target, Award } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import PageContainer from "@/components/layout/PageContainer"
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from "recharts"

export default function MidLeaderSelf360() {
  const [selectedRound, setSelectedRound] = useState("2024-Q3")

  const radarData = [
    { subject: "리더십", A: 4.2, fullMark: 5 },
    { subject: "커뮤니케이션", A: 3.8, fullMark: 5 },
    { subject: "문제해결", A: 4.5, fullMark: 5 },
    { subject: "팀워크", A: 4.0, fullMark: 5 },
    { subject: "혁신성", A: 3.6, fullMark: 5 },
    { subject: "전략적사고", A: 4.1, fullMark: 5 },
  ]

  const feedbackSummary = [
    {
      category: "상급자 피드백",
      icon: TrendingUp,
      score: 4.3,
      highlight: "전략적 사고와 리더십 역량이 뛰어남",
      color: "text-blue-600",
    },
    {
      category: "동료 피드백",
      icon: Users,
      score: 3.9,
      highlight: "협업 능력과 커뮤니케이션 개선 필요",
      color: "text-green-600",
    },
    {
      category: "하급자 피드백",
      icon: Target,
      score: 4.1,
      highlight: "팀원들에게 동기부여를 잘 제공함",
      color: "text-purple-600",
    },
    {
      category: "자기평가",
      icon: Award,
      score: 3.8,
      highlight: "지속적인 성장과 학습에 대한 의지",
      color: "text-orange-600",
    },
  ]

  return (
    <PageContainer title="360° Review - 중간리더 본인 결과 조회">
      {/* Round Selection */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Select value={selectedRound} onValueChange={setSelectedRound}>
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2024-Q1">2024년 1분기</SelectItem>
              <SelectItem value="2024-Q2">2024년 2분기</SelectItem>
              <SelectItem value="2024-Q3">2024년 3분기</SelectItem>
              <SelectItem value="2024-Q4">2024년 4분기</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Badge variant="secondary" className="text-sm">
          조회 전용 - 편집 불가
        </Badge>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Overall Score Card */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Award className="h-5 w-5 text-[var(--primary)]" />
              종합 점수
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-center">
              <div className="text-4xl font-bold text-[var(--primary)] mb-2">4.0</div>
              <div className="text-sm text-muted-foreground mb-4">5점 만점</div>
              <Progress value={80} className="w-full" />
              <p className="text-sm text-muted-foreground mt-2">전체 평균 대비 상위 25% 수준</p>
            </div>
          </CardContent>
        </Card>

        {/* Competency Radar Chart */}
        <Card>
          <CardHeader>
            <CardTitle>핵심 역량 분석</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
                <PolarRadiusAxis angle={90} domain={[0, 5]} tick={{ fontSize: 10 }} />
                <Radar name="점수" dataKey="A" stroke="#5277F1" fill="#5277F1" fillOpacity={0.3} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Feedback Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {feedbackSummary.map((feedback, index) => {
          const Icon = feedback.icon
          return (
            <Card key={index}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Icon className={`h-5 w-5 ${feedback.color}`} />
                    <h3 className="font-semibold">{feedback.category}</h3>
                  </div>
                  <Badge variant="outline" className="text-lg font-bold">
                    {feedback.score}
                  </Badge>
                </div>
                <p className="text-sm text-muted-foreground">{feedback.highlight}</p>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Detailed Feedback Section */}
      <Card>
        <CardHeader>
          <CardTitle>상세 피드백 요약</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="border-l-4 border-green-500 pl-4">
            <h4 className="font-semibold text-green-700 mb-2">강점</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• 전략적 사고와 장기적 비전 제시 능력이 뛰어남</li>
              <li>• 팀원들의 성장을 위한 코칭과 멘토링 역량 우수</li>
              <li>• 복잡한 문제 상황에서의 의사결정 능력이 탁월함</li>
            </ul>
          </div>

          <div className="border-l-4 border-orange-500 pl-4">
            <h4 className="font-semibold text-orange-700 mb-2">개선 영역</h4>
            <ul className="text-sm text-muted-foreground space-y-1">
              <li>• 동료들과의 수평적 커뮤니케이션 스킬 향상 필요</li>
              <li>• 혁신적 아이디어 도출과 실행 과정에서의 리스크 관리</li>
              <li>• 변화 관리 상황에서의 팀원 동기부여 방법 개선</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </PageContainer>
  )
}
