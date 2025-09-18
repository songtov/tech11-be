"use client"

import { Clock, ChevronDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import SearchBox from "@/components/common/SearchBox"
import { useUiStore } from "@/stores/useUiStore"
import { useRouter } from "next/navigation"

export default function Header() {
  const { recentVisited } = useUiStore()
  const router = useRouter()

  const handleRecentPageClick = (path: string) => {
    router.push(path)
  }

  return (
    <header className="h-20 bg-background border-b border-border flex items-center justify-between px-6 sticky top-0 z-50">
      {/* Left: Logo/Title */}
      <div className="flex items-center">
        <h1 className="text-xl font-bold text-[#5277F1]">MyHR</h1>
      </div>

      {/* Center: Enhanced Search */}
      <SearchBox />

      {/* Right: Recent Pages, Privacy Policy, Profile */}
      <div className="flex items-center gap-2">
        {/* Recent Pages */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="sm">
              <Clock className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64">
            {recentVisited.slice(0, 10).map((page) => (
              <DropdownMenuItem key={page.id} onClick={() => handleRecentPageClick(page.path)}>
                <div className="flex flex-col">
                  <span className="font-medium">{page.title}</span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(page.visitedAt).toLocaleString("ko-KR", {
                      month: "short",
                      day: "numeric",
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
              </DropdownMenuItem>
            ))}
            {recentVisited.length === 0 && <DropdownMenuItem disabled>최근 방문한 페이지가 없습니다</DropdownMenuItem>}
          </DropdownMenuContent>
        </DropdownMenu>

        {/* Privacy Policy */}
        <Button variant="ghost" size="sm">
          개인정보처리방침
        </Button>

        {/* Profile */}
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="flex items-center gap-2 px-2">
              <Avatar className="h-8 w-8">
                <AvatarImage src="/quokka.jpg" />
                <AvatarFallback>강</AvatarFallback>
              </Avatar>
              <div className="flex flex-col items-start">
                <span className="text-sm font-medium">강성운</span>
                <Badge variant="secondary" className="text-xs">
                  사원
                </Badge>
              </div>
              <ChevronDown className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem>내 정보</DropdownMenuItem>
            <DropdownMenuItem>로그아웃</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
