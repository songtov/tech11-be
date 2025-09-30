"use client"

import { useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { ArrowLeft, Save, Send, Star } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Label } from "@/components/ui/label"
import PageContainer from "@/components/layout/PageContainer"
import { usePerformanceStore } from "../store/usePerformanceStore"

export default function ReviewDetail() {
  const router = useRouter()
  const params = useParams()
  const { reviews } = usePerformanceStore()
  const [activeTab, setActiveTab] = useState("self")

  const reviewId = params.reviewId as string
  const review = reviews.find((r) => r.id === reviewId)

  const [selfEvaluation, setSelfEvaluation] = useState({
    scores: { leadership: 4, communication: 3, performance: 4, collaboration: 5 },
    comments: "올해는 특히 팀 리더십과 프로젝트 관리 능력이 향상되었다고 생각합니다...",
  })

  const [supervisorEvaluation, setSupervisorEvaluation] = useState({
    scores: { leadership: 4, communication: 4, performance: 4, collaboration: 4 },
    comments: "전반적으로 우수한 성과를 보여주었으며, 특히 팀워크 부분에서 뛰어난 모습을 보였습니다...",
  })

  if (!review) {
    return (
      <PageContainer title="평가 상세">
        <Card>
          <CardContent className="text-center py-12">
            <p className="text-muted-foreground">평가를 찾을 수 없습니다.</p>
            <Button onClick={() => router.back()} className="mt-4">
              <ArrowLeft className="h-4 w-4 mr-2" />
              돌아가기
            </Button>
          </CardContent>
        </Card>
      </PageContainer>
    )
  }

  const renderStarRating = (score: number, onChange?: (score: number) => void, readonly = false) => {
    return (
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            type="button"
            disabled={readonly}
            onClick={() => onChange?.(star)}
            className={`${
              star <= score ? "text-yellow-400" : "text-gray-300"
            } ${readonly ? "cursor-default" : "hover:text-yellow-400 cursor-pointer"}`}
          >
            <Star className="h-5 w-5 fill-current" />
          </button>
        ))}
      </div>
    )
  }

  const isSubmitted = review.status === "submitted" || review.status === "approved"

  return (
    <PageContainer title={`평가 상세 - ${review.title}`}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <Button variant="ghost" onClick={() => router.back()}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            평가 목록으로
          </Button>

          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-sm">
              {review.round}
            </Badge>
            <Badge variant={review.status === "approved" ? "default" : "secondary"}>
              {review.status === "approved" ? "승인됨" : review.status === "submitted" ? "제출됨" : "작성중"}
            </Badge>
          </div>
        </div>

        {/* Review Info */}
        <Card>
          <CardHeader>
            <CardTitle>{review.title}</CardTitle>
            <div className="text-sm text-muted-foreground">
              평가 기간: {review.round} | 마감일: {review.dueDate}
            </div>
          </CardHeader>
        </Card>

        {/* Evaluation Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="self">자기평가</TabsTrigger>
            <TabsTrigger value="supervisor">상사평가</TabsTrigger>
          </TabsList>

          <TabsContent value="self" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>자기평가</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Competency Ratings */}
                <div className="space-y-4">
                  <h3 className="font-medium">핵심 역량 평가</h3>

                  {Object.entries(selfEvaluation.scores).map(([key, score]) => (
                    <div key={key} className="flex items-center justify-between">
                      <Label className="text-sm font-medium">
                        {key === "leadership"
                          ? "리더십"
                          : key === "communication"
                            ? "의사소통"
                            : key === "performance"
                              ? "업무성과"
                              : "협업능력"}
                      </Label>
                      {renderStarRating(
                        score,
                        (newScore) =>
                          setSelfEvaluation((prev) => ({
                            ...prev,
                            scores: { ...prev.scores, [key]: newScore },
                          })),
                        isSubmitted,
                      )}
                    </div>
                  ))}
                </div>

                {/* Comments */}
                <div className="space-y-2">
                  <Label htmlFor="self-comments">종합 의견</Label>
                  <Textarea
                    id="self-comments"
                    value={selfEvaluation.comments}
                    onChange={(e) => setSelfEvaluation((prev) => ({ ...prev, comments: e.target.value }))}
                    placeholder="자기평가에 대한 상세한 의견을 작성해주세요..."
                    rows={6}
                    disabled={isSubmitted}
                  />
                </div>

                {!isSubmitted && (
                  <div className="flex gap-2 pt-4">
                    <Button variant="outline">
                      <Save className="h-4 w-4 mr-2" />
                      임시저장
                    </Button>
                    <Button>
                      <Send className="h-4 w-4 mr-2" />
                      제출하기
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="supervisor" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>상사평가</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {review.status === "approved" ? (
                  <>
                    {/* Competency Ratings */}
                    <div className="space-y-4">
                      <h3 className="font-medium">핵심 역량 평가</h3>

                      {Object.entries(supervisorEvaluation.scores).map(([key, score]) => (
                        <div key={key} className="flex items-center justify-between">
                          <Label className="text-sm font-medium">
                            {key === "leadership"
                              ? "리더십"
                              : key === "communication"
                                ? "의사소통"
                                : key === "performance"
                                  ? "업무성과"
                                  : "협업능력"}
                          </Label>
                          {renderStarRating(score, undefined, true)}
                        </div>
                      ))}
                    </div>

                    {/* Comments */}
                    <div className="space-y-2">
                      <Label>상사 의견</Label>
                      <div className="p-3 bg-muted rounded-md">
                        <p className="text-sm">{supervisorEvaluation.comments}</p>
                      </div>
                    </div>

                    {/* Final Score */}
                    <div className="p-4 bg-primary/5 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">최종 평가 점수</span>
                        <span className="text-2xl font-bold text-primary">{review.score}/5.0</span>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-muted-foreground">상사평가는 자기평가 제출 후 확인할 수 있습니다.</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </PageContainer>
  )
}
