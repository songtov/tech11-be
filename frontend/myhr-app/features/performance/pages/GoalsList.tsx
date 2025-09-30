"use client"

import { useState } from "react"
import { Plus, Target } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import PageContainer from "@/components/layout/PageContainer"
import GoalCard from "../components/GoalCard"
import { usePerformanceStore } from "../store/usePerformanceStore"

export default function GoalsList() {
  const { goals, goalFilters, setGoalFilters } = usePerformanceStore()
  const [selectedStatus, setSelectedStatus] = useState("all")

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
        return "전체"
    }
  }

  const filteredGoals = goals.filter((goal) => {
    if (selectedStatus === "all") return true
    return goal.status === selectedStatus
  })

  return (
    <PageContainer title="목표 관리">
      {/* Filters and Actions */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Select value={goalFilters.year} onValueChange={(value) => setGoalFilters({ year: value })}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="2024">2024년</SelectItem>
              <SelectItem value="2023">2023년</SelectItem>
            </SelectContent>
          </Select>

          <Select value={goalFilters.quarter} onValueChange={(value) => setGoalFilters({ quarter: value })}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Q1">1분기</SelectItem>
              <SelectItem value="Q2">2분기</SelectItem>
              <SelectItem value="Q3">3분기</SelectItem>
              <SelectItem value="Q4">4분기</SelectItem>
            </SelectContent>
          </Select>

          <Select value={selectedStatus} onValueChange={setSelectedStatus}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">전체</SelectItem>
              <SelectItem value="in-progress">진행중</SelectItem>
              <SelectItem value="completed">완료</SelectItem>
              <SelectItem value="delayed">지연</SelectItem>
              <SelectItem value="at_risk">위험</SelectItem>
              <SelectItem value="overdue">지연</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Button>
          <Plus className="h-4 w-4 mr-2" />새 목표 추가
        </Button>
      </div>

      {/* Goals Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {filteredGoals.map((goal) => (
          <GoalCard key={goal.id} goal={goal} />
        ))}
      </div>

      {filteredGoals.length === 0 && (
        <Card className="text-center py-12">
          <CardContent>
            <Target className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <h3 className="text-lg font-medium mb-2">목표가 없습니다</h3>
            <p className="text-muted-foreground mb-4">새로운 목표를 추가해보세요.</p>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              목표 추가
            </Button>
          </CardContent>
        </Card>
      )}
    </PageContainer>
  )
}
