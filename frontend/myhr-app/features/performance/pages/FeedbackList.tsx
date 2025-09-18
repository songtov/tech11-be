"use client"
import { Plus, MessageSquare, Send, Inbox, Clock } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import PageContainer from "@/components/layout/PageContainer"
import { usePerformanceStore } from "../store/usePerformanceStore"

export default function FeedbackList() {
  const { feedbacks } = usePerformanceStore()

  const receivedFeedbacks = feedbacks.filter((f) => f.toId === "user1")
  const sentFeedbacks = feedbacks.filter((f) => f.fromId === "user1")

  const getTypeColor = (type: string) => {
    switch (type) {
      case "positive":
        return "bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/20"
      case "constructive":
        return "bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/20"
      case "request":
        return "bg-[var(--primary)]/10 text-[var(--primary)] border-[var(--primary)]/20"
      default:
        return "bg-muted text-muted-foreground"
    }
  }

  const getTypeLabel = (type: string) => {
    switch (type) {
      case "positive":
        return "긍정적"
      case "constructive":
        return "건설적"
      case "request":
        return "요청"
      default:
        return type
    }
  }

  const FeedbackCard = ({ feedback, isReceived }: { feedback: any; isReceived: boolean }) => (
    <Card
      className={`hover:shadow-md transition-shadow ${!feedback.read && isReceived ? "border-[var(--primary)]" : ""}`}
    >
      <CardContent className="p-4">
        <div className="flex items-start gap-4">
          <Avatar className="h-10 w-10">
            <AvatarImage src="/placeholder.svg" />
            <AvatarFallback>{isReceived ? feedback.fromName[0] : feedback.toName[0]}</AvatarFallback>
          </Avatar>

          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h4 className="font-medium">{feedback.title}</h4>
                <p className="text-sm text-muted-foreground">
                  {isReceived ? `${feedback.fromName}님으로부터` : `${feedback.toName}님에게`}
                </p>
              </div>

              <div className="flex items-center gap-2">
                {!feedback.read && isReceived && <div className="w-2 h-2 bg-[var(--primary)] rounded-full"></div>}
                <Badge variant="outline" className={getTypeColor(feedback.type)}>
                  {getTypeLabel(feedback.type)}
                </Badge>
              </div>
            </div>

            <p className="text-sm text-muted-foreground mb-3 line-clamp-2">{feedback.content}</p>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                {new Date(feedback.createdAt).toLocaleDateString("ko-KR")}
              </div>

              <Button variant="ghost" size="sm">
                상세 보기
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )

  return (
    <PageContainer title="피드백">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-[var(--primary)]" />
            <span className="font-medium">피드백 관리</span>
          </div>
        </div>

        <Button>
          <Plus className="h-4 w-4 mr-2" />
          피드백 작성
        </Button>
      </div>

      <Tabs defaultValue="received" className="space-y-6">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="received" className="flex items-center gap-2">
            <Inbox className="h-4 w-4" />
            받은 피드백 ({receivedFeedbacks.length})
          </TabsTrigger>
          <TabsTrigger value="sent" className="flex items-center gap-2">
            <Send className="h-4 w-4" />
            보낸 피드백 ({sentFeedbacks.length})
          </TabsTrigger>
          <TabsTrigger value="requests">요청함 (0)</TabsTrigger>
        </TabsList>

        <TabsContent value="received" className="space-y-4">
          {receivedFeedbacks.map((feedback) => (
            <FeedbackCard key={feedback.id} feedback={feedback} isReceived={true} />
          ))}

          {receivedFeedbacks.length === 0 && (
            <Card className="text-center py-12">
              <CardContent>
                <Inbox className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">받은 피드백이 없습니다</h3>
                <p className="text-muted-foreground">동료들에게 피드백을 요청해보세요.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="sent" className="space-y-4">
          {sentFeedbacks.map((feedback) => (
            <FeedbackCard key={feedback.id} feedback={feedback} isReceived={false} />
          ))}

          {sentFeedbacks.length === 0 && (
            <Card className="text-center py-12">
              <CardContent>
                <Send className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                <h3 className="text-lg font-medium mb-2">보낸 피드백이 없습니다</h3>
                <p className="text-muted-foreground">동료들에게 피드백을 작성해보세요.</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="requests">
          <Card className="text-center py-12">
            <CardContent>
              <MessageSquare className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <h3 className="text-lg font-medium mb-2">피드백 요청이 없습니다</h3>
              <p className="text-muted-foreground">필요한 피드백을 요청해보세요.</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </PageContainer>
  )
}
