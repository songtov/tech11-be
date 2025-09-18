"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Search, User, Menu } from "lucide-react"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { cn } from "@/lib/utils"

type SearchMode = "employee" | "menu"

interface Employee {
  id: string
  name: string
  department: string
  position: string
  avatar?: string
}

interface MenuResult {
  id: string
  label: string
  path: string
  section: string
}

const mockEmployees: Employee[] = [
  { id: "1", name: "김직원", department: "인사팀", position: "대리" },
  { id: "2", name: "이매니저", department: "개발팀", position: "과장" },
  { id: "3", name: "박팀장", department: "마케팅팀", position: "팀장" },
  { id: "4", name: "최사원", department: "영업팀", position: "사원" },
  { id: "5", name: "정부장", department: "기획팀", position: "부장" },
  { id: "6", name: "강성운", department: "사장", position: "임원" },
  { id: "7", name: "최서영", department: "CCO", position: "임원" },
  { id: "8", name: "함영재", department: "기업문화부문", position: "임원" },
  { id: "9", name: "김철수", department: "대표이사", position: "임원" }
]

const mockMenuResults: MenuResult[] = [
  { id: "1", label: "성과 대시보드", path: "/performance", section: "성과관리" },
  { id: "2", label: "목표 관리", path: "/performance/goals", section: "성과관리" },
  { id: "3", label: "평가 관리", path: "/performance/reviews", section: "성과관리" },
  { id: "4", label: "피드백", path: "/performance/feedback", section: "성과관리" },
  { id: "5", label: "근태 관리", path: "/attendance", section: "근태" },
]

export default function SearchBox() {
  const [query, setQuery] = useState("")
  const [mode, setMode] = useState<SearchMode>("employee")
  const [isOpen, setIsOpen] = useState(false)
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const inputRef = useRef<HTMLInputElement>(null)
  const resultsRef = useRef<HTMLDivElement>(null)

  const filteredEmployees = mockEmployees
    .filter(
      (emp) =>
        emp.name.toLowerCase().includes(query.toLowerCase()) ||
        emp.department.toLowerCase().includes(query.toLowerCase()) ||
        emp.position.toLowerCase().includes(query.toLowerCase()),
    )
    .slice(0, 5)

  const filteredMenus = mockMenuResults
    .filter(
      (menu) =>
        menu.label.toLowerCase().includes(query.toLowerCase()) ||
        menu.section.toLowerCase().includes(query.toLowerCase()),
    )
    .slice(0, 5)

  const results = mode === "employee" ? filteredEmployees : filteredMenus
  const maxResults = Math.min(results.length, 5)

  useEffect(() => {
    if (isOpen && query) {
      setSelectedIndex(-1)
    }
  }, [query, mode, isOpen])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen) return

    switch (e.key) {
      case "ArrowDown":
        e.preventDefault()
        setSelectedIndex((prev) => (prev < maxResults - 1 ? prev + 1 : prev))
        break
      case "ArrowUp":
        e.preventDefault()
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1))
        break
      case "Enter":
        e.preventDefault()
        if (selectedIndex >= 0 && results[selectedIndex]) {
          handleResultClick(results[selectedIndex])
        }
        break
      case "Escape":
        setIsOpen(false)
        inputRef.current?.blur()
        break
    }
  }

  const handleResultClick = (result: any) => {
    if (mode === "employee") {
      console.log("[v0] Employee selected:", result.name)
      // Navigate to employee profile or perform action
    } else {
      console.log("[v0] Menu selected:", result.path)
      // Navigate to menu path
      window.location.href = result.path
    }
    setIsOpen(false)
    setQuery("")
  }

  return (
    <div className="relative flex-1 max-w-md mx-8">
      {/* Search Mode Toggle */}
      <div className="flex mb-2">
        <Button
          variant={mode === "employee" ? "default" : "ghost"}
          size="sm"
          onClick={() => setMode("employee")}
          className="rounded-r-none"
        >
          <User className="h-3 w-3 mr-1" />
          직원
        </Button>
        <Button
          variant={mode === "menu" ? "default" : "ghost"}
          size="sm"
          onClick={() => setMode("menu")}
          className="rounded-l-none"
        >
          <Menu className="h-3 w-3 mr-1" />
          메뉴
        </Button>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          ref={inputRef}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsOpen(true)}
          onBlur={() => setTimeout(() => setIsOpen(false), 200)}
          onKeyDown={handleKeyDown}
          placeholder={mode === "employee" ? "직원 이름, 부서 검색" : "메뉴 검색"}
          className="pl-10 pr-4"
        />
      </div>

      {/* Search Results */}
      {isOpen && query && (
        <div
          ref={resultsRef}
          className="absolute top-full left-0 right-0 mt-1 bg-background border border-border rounded-md shadow-lg z-50 max-h-80 overflow-y-auto"
        >
          {results.length === 0 ? (
            <div className="p-4 text-center text-muted-foreground">검색 결과가 없습니다</div>
          ) : (
            <div className="py-2">
              {mode === "employee"
                ? // Employee Results
                  (results as Employee[]).map((employee, index) => (
                    <button
                      key={employee.id}
                      className={cn(
                        "w-full px-4 py-3 text-left hover:bg-muted flex items-center gap-3",
                        selectedIndex === index && "bg-muted",
                      )}
                      onClick={() => handleResultClick(employee)}
                    >
                      <Avatar className="h-8 w-8">
                        <AvatarImage src={employee.avatar || "/placeholder.svg"} />
                        <AvatarFallback>{employee.name[0]}</AvatarFallback>
                      </Avatar>
                      <div className="flex-1">
                        <div className="font-medium">{employee.name}</div>
                        <div className="text-sm text-muted-foreground">
                          {employee.department} · {employee.position}
                        </div>
                      </div>
                    </button>
                  ))
                : // Menu Results
                  (results as MenuResult[]).map((menu, index) => (
                    <button
                      key={menu.id}
                      className={cn("w-full px-4 py-3 text-left hover:bg-muted", selectedIndex === index && "bg-muted")}
                      onClick={() => handleResultClick(menu)}
                    >
                      <div className="font-medium">{menu.label}</div>
                      <div className="text-sm text-muted-foreground">{menu.section}</div>
                    </button>
                  ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
