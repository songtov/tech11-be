"use client"

import { useState } from "react"
import { useRouter, usePathname } from "next/navigation"
import { Plus, FileText, Calendar, Clock } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import PageContainer from "@/components/layout/PageContainer"
import { usePerformanceStore } from "../store/usePerformanceStore"

export default function ReviewsList() {
  const { reviews } = usePerformanceStore()
  const [selectedRound, setSelectedRound] = useState("all")
  const router = useRouter()
  const pathname = usePathname()

  const getCurrentTab = () => {
    if (pathname.includes("/peers")) return "peers"
    if (pathname.includes("/history")) return "history"
    return "me"
  }

  const handleTabChange = (value: string) => {
    const basePath = "/performance/reviews"
    if (value === "me") {
      router.push(`${basePath}/me`)
    } else {
      router.push(`${basePath}/${value}`)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "approved":
        return "bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/20"
      case "submitted":
        return "bg-[var(--primary)]/10 text-[var(--primary)] border-[var(--primary)]/20"
      case "draft":
        return "bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/20"
      case "needs_changes":
        return "bg-[var(--danger)]/10 text-[var(--danger)] border-[var(--danger)]/20"
      default:
        return "bg-muted text-muted-foreground"
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case "approved":
        return "승인됨"
      case "submitted":
        return "제출됨"
      case "draft":
        return "작성중"
      case "needs_changes":
        return "수정필요"
      case "idle":
        return "미작성"
      default:
        return status
    }
  }

  const filteredReviews = selectedRound === "all" ? reviews : reviews.filter((review) => review.round === selectedRound)

  return (
    <PageContainer title="평가 관리">
      <Tabs value={getCurrentTab()} onValueChange={handleTabChange} className="w-full">
        <TabsList className="grid w-full grid-cols-3 mb-6">
          <TabsTrigger value="me">나의 평가</TabsTrigger>
          <TabsTrigger value="peers">동료·중간 평가</TabsTrigger>
          <TabsTrigger value="history">평가 이력</TabsTrigger>
        </TabsList>

        <TabsContent value="me" className="space-y-6">
          {/* Filters and Actions */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Select value={selectedRound} onValueChange={setSelectedRound}>
                <SelectTrigger className="w-48">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체 라운드</SelectItem>
                  <SelectItem value="2024-Q1">2024년 1분기</SelectItem>
                  <SelectItem value="2024-Q2">2024년 2분기</SelectItem>
                  <SelectItem value="2024-Q3">2024년 3분기</SelectItem>
                  <SelectItem value="2024-Q4">2024년 4분기</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <Button>
              <Plus className="h-4 w-4 mr-2" />새 평가 시작
            </Button>
          </div>

          {/* Reviews List */}
          <div className="space-y-4">
            {filteredReviews.map((review) => (
              <Card key={review.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="p-2 bg-[var(--primary)]/10 rounded-lg">
                        <FileText className="h-5 w-5 text-[var(--primary)]" />
                      </div>

                      <div className="flex-1">
                        <h3 className="font-semibold text-lg">{review.title}</h3>
                        <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            라운드: {review.round}
                          </div>
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            마감: {review.dueDate}
                          </div>
                          {review.score && (
                            <div className="flex items-center gap-1">
                              <span>점수: {review.score}/5.0</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      <Badge variant="outline" className={getStatusColor(review.status)}>
                        {getStatusLabel(review.status)}
                      </Badge>

                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => router.push(`/performance/reviews/${review.id}`)}
                        >
                          상세 보기
                        </Button>
                        {review.status === "draft" && (
                          <Button size="sm" onClick={() => router.push(`/performance/reviews/${review.id}`)}>
                            계속 작성
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {filteredReviews.length === 0 && (
            <Card className="text-center py-12">
              <CardContent>
                <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">평가가 없습니다</h3>
                <p className="text-muted-foreground mb-4">새로운 평가를 시작해보세요.</p>
                <Button>
                  <Plus className="h-4 w-4 mr-2" />
                  평가 시작
                </Button>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="peers" className="space-y-6">
          <Card className="text-center py-12">
            <CardContent>
              <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">동료·중간 평가</h3>
              <p className="text-muted-foreground">동료 및 중간 관리자 평가 목록이 여기에 표시됩니다.</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="history" className="space-y-6">
          <Card className="text-center py-12">
            <CardContent>
              <FileText className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">평가 이력</h3>
              <p className="text-muted-foreground">과거 평가 이력이 여기에 표시됩니다.</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </PageContainer>
  )
}
