"use client"

import { useRouter } from "next/navigation"
import { Calendar, User, TrendingUp } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"
import type { Goal } from "../store/usePerformanceStore"

interface GoalCardProps {
  goal: Goal
}

export default function GoalCard({ goal }: GoalCardProps) {
  const router = useRouter()

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/20"
      case "in-progress":
        return "bg-[var(--primary)]/10 text-[var(--primary)] border-[var(--primary)]/20"
      case "delayed":
      case "overdue":
        return "bg-[var(--danger)]/10 text-[var(--danger)] border-[var(--danger)]/20"
      case "at_risk":
        return "bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/20"
      default:
        return "bg-muted text-muted-foreground"
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "completed":
        return "완료"
      case "in-progress":
        return "진행중"
      case "delayed":
        return "지연"
      case "at_risk":
        return "위험"
      case "overdue":
        return "지연"
      default:
        return status
    }
  }

  const getPriorityLabel = (priority: string) => {
    switch (priority) {
      case "high":
        return "높음"
      case "medium":
        return "보통"
      case "low":
        return "낮음"
      default:
        return priority
    }
  }

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg mb-2">{goal.title}</CardTitle>
            <p className="text-sm text-muted-foreground">{goal.description}</p>
          </div>
          <div className="flex flex-col gap-2">
            <Badge variant="outline" className={getStatusColor(goal.status)}>
              {getStatusLabel(goal.status)}
            </Badge>
            <Badge variant="secondary" className="text-xs">
              {getPriorityLabel(goal.priority)}
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Progress */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">진행률</span>
            <span className="text-sm text-muted-foreground">{goal.progress}%</span>
          </div>
          <Progress value={goal.progress} className="h-2" />
        </div>

        {/* Meta Info */}
        <div className="flex items-center gap-4 text-sm text-muted-foreground">
          <div className="flex items-center gap-1">
            <User className="h-3 w-3" />
            {goal.ownerName}
          </div>
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            {goal.dueDate}
          </div>
        </div>

        {/* Category */}
        {goal.category && (
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">카테고리:</span>
            <Badge variant="outline" className="text-xs">
              {goal.category}
            </Badge>
          </div>
        )}

        {/* KPIs */}
        <div className="space-y-2">
          <h4 className="text-sm font-medium flex items-center gap-1">
            <TrendingUp className="h-3 w-3" />
            핵심 지표
          </h4>
          {goal.kpis.slice(0, 2).map((kpi, index) => (
            <div key={index} className="flex items-center justify-between text-sm">
              <span>{kpi.name}</span>
              <span className="font-medium">
                {kpi.current.toLocaleString()} / {kpi.target.toLocaleString()} {kpi.unit}
              </span>
            </div>
          ))}
          {goal.kpis.length > 2 && <p className="text-xs text-muted-foreground">+{goal.kpis.length - 2}개 더</p>}
        </div>

        {/* Actions */}
        <div className="flex gap-2 pt-2">
          <Button
            variant="outline"
            size="sm"
            className="flex-1 bg-transparent"
            onClick={() => router.push(`/performance/goals/${goal.id}`)}
          >
            상세 보기
          </Button>
          <Button size="sm" className="flex-1" onClick={() => router.push(`/performance/goals/${goal.id}`)}>
            편집
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
