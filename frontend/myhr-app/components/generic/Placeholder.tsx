"use client"

import { useRouter } from "next/navigation"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Construction, ArrowLeft } from "lucide-react"

interface PlaceholderProps {
  title?: string
  description?: string
}

export default function Placeholder({
  title = "준비 중인 기능",
  description = "이 기능은 현재 개발 중입니다.",
}: PlaceholderProps) {
  const router = useRouter()

  return (
    <div className="flex items-center justify-center min-h-[60vh] p-6">
      <Card className="w-full max-w-md text-center">
        <CardHeader>
          <div className="mx-auto mb-4 p-3 bg-muted rounded-full w-fit">
            <Construction className="h-8 w-8 text-muted-foreground" />
          </div>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-muted-foreground">{description}</p>
          <p className="text-sm text-muted-foreground">곧 업데이트될 예정입니다.</p>
          <Button variant="outline" onClick={() => router.back()} className="w-full">
            <ArrowLeft className="h-4 w-4 mr-2" />
            이전으로
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
