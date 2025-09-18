"use client"

import { useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { ArrowLeft, Edit, Target, Calendar, TrendingUp, MessageSquare } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import PageContainer from "@/components/layout/PageContainer"
import { usePerformanceStore } from "../store/usePerformanceStore"

export default function GoalDetail() {
  const router = useRouter()
  const params = useParams()
  const { goals } = usePerformanceStore()
  const [isEditing, setIsEditing] = useState(false)

  const goalId = params.goalId as string
  const goal = goals.find((g) => g.id === goalId)

  const [editedGoal, setEditedGoal] = useState(goal || {})

  if (!goal) {
    return (
      <PageContainer title="목표 상세">
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-muted-foreground">목표를 찾을 수 없습니다.</p>
            <Button onClick={() => router.back()} className="mt-4">
              <ArrowLeft className="h-4 w-4 mr-2" />
              돌아가기
            </Button>
          </CardContent>
        </Card>
      </PageContainer>
    )
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-800 border-green-200"
      case "in_progress":
        return "bg-blue-100 text-blue-800 border-blue-200"
      case "at_risk":
        return "bg-yellow-100 text-yellow-800 border-yellow-200"
      case "overdue":
        return "bg-red-100 text-red-800 border-red-200"
      default:
        return "bg-gray-100 text-gray-800 border-gray-200"
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "completed":
        return "완료"
      case "in_progress":
        return "진행중"
      case "at_risk":
        return "위험"
      case "overdue":
        return "지연"
      default:
        return status
    }
  }

  return (
    <PageContainer title={`목표 상세 - ${goal.title}`}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            목표 목록으로
          </Button>

          <div className="flex items-center gap-2">
            <Badge variant="outline" className={getStatusColor(goal.status)}>
              {getStatusLabel(goal.status)}
            </Badge>
            <Button variant={isEditing ? "default" : "outline"} onClick={() => setIsEditing(!isEditing)}>
              <Edit className="h-4 w-4 mr-2" />
              {isEditing ? "저장" : "편집"}
            </Button>
          </div>
        </div>

        {/* Goal Overview */}
        <Card>
          <CardHeader>
            <div className="flex items-start gap-4">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Target className="h-6 w-6 text-primary" />
              </div>
              <div className="flex-1">
                {isEditing ? (
                  <Input
                    value={editedGoal.title || ""}
                    onChange={(e) => setEditedGoal((prev) => ({ ...prev, title: e.target.value }))}
                    className="text-xl font-semibold"
                  />
                ) : (
                  <CardTitle className="text-xl">{goal.title}</CardTitle>
                )}
                <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    마감: {goal.dueDate}
                  </div>
                  <div className="flex items-center gap-1">
                    <TrendingUp className="h-3 w-3" />
                    진행률: {goal.progress}%
                  </div>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label>진행률</Label>
                <span className="text-sm font-medium">{goal.progress}%</span>
              </div>
              <Progress value={goal.progress} className="h-2" />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label>목표 설명</Label>
              {isEditing ? (
                <Textarea
                  value={editedGoal.description || ""}
                  onChange={(e) => setEditedGoal((prev) => ({ ...prev, description: e.target.value }))}
                  rows={4}
                />
              ) : (
                <p className="text-sm text-muted-foreground p-3 bg-muted rounded-md">
                  {goal.description || "목표 설명이 없습니다."}
                </p>
              )}
            </div>

            {/* Key Results */}
            <div className="space-y-2">
              <Label>핵심 성과 지표 (KR)</Label>
              <div className="space-y-2">
                {goal.keyResults?.map((kr, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <span className="text-sm">{kr.title}</span>
                    <div className="flex items-center gap-2">
                      <Progress value={kr.progress} className="w-20 h-1" />
                      <span className="text-xs text-muted-foreground">{kr.progress}%</span>
                    </div>
                  </div>
                )) || (
                  <p className="text-sm text-muted-foreground p-3 bg-muted rounded-md">
                    핵심 성과 지표가 설정되지 않았습니다.
                  </p>
                )}
              </div>
            </div>

            {/* Priority and Category */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>우선순위</Label>
                {isEditing ? (
                  <Select
                    value={editedGoal.priority || ""}
                    onValueChange={(value) => setEditedGoal((prev) => ({ ...prev, priority: value }))}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="high">높음</SelectItem>
                      <SelectItem value="medium">보통</SelectItem>
                      <SelectItem value="low">낮음</SelectItem>
                    </SelectContent>
                  </Select>
                ) : (
                  <Badge variant="outline">
                    {goal.priority === "high" ? "높음" : goal.priority === "medium" ? "보통" : "낮음"}
                  </Badge>
                )}
              </div>

              <div className="space-y-2">
                <Label>카테고리</Label>
                {isEditing ? (
                  <Input
                    value={editedGoal.category || ""}
                    onChange={(e) => setEditedGoal((prev) => ({ ...prev, category: e.target.value }))}
                  />
                ) : (
                  <Badge variant="secondary">{goal.category || "미분류"}</Badge>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Comments/Updates */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              진행 상황 업데이트
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Textarea placeholder="목표 진행 상황에 대한 업데이트를 작성해주세요..." rows={3} />
              <Button size="sm">업데이트 추가</Button>
            </div>

            {/* Previous Updates */}
            <div className="mt-6 space-y-3">
              <h4 className="font-medium text-sm">이전 업데이트</h4>
              <div className="space-y-3">
                <div className="p-3 border-l-4 border-primary/20 bg-muted/50">
                  <p className="text-sm">
                    Q3 중간 점검: 목표 달성률 75% 도달. 예상보다 빠른 진행으로 목표 달성 가능성 높음.
                  </p>
                  <p className="text-xs text-muted-foreground mt-1">2024-09-15</p>
                </div>
                <div className="p-3 border-l-4 border-primary/20 bg-muted/50">
                  <p className="text-sm">Q2 검토: 일부 KR에서 지연 발생. 추가 리소스 투입 및 일정 조정 필요.</p>
                  <p className="text-xs text-muted-foreground mt-1">2024-06-30</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
