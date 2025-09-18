"use client"

import type React from "react"

import { useState } from "react"
import { useAuth } from "@/hooks/use-auth"
import { useAXToast } from "@/hooks/use-toast"
import { X, Eye, EyeOff } from "lucide-react"
import { cn } from "@/lib/utils"

interface LoginModalProps {
  isOpen: boolean
  onClose: () => void
}

export function LoginModal({ isOpen, onClose }: LoginModalProps) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { login } = useAuth()
  const { toast } = useAXToast()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) return

    setIsSubmitting(true)
    try {
      await login(email, password)
      toast({
        title: "로그인 성공",
        description: "AX College에 오신 것을 환영합니다!",
      })
      onClose()
      setEmail("")
      setPassword("")
    } catch (error) {
      toast({
        title: "로그인 실패",
        description: error instanceof Error ? error.message : "로그인에 실패했습니다.",
        variant: "destructive",
      })
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="ax-card w-full max-w-md p-6">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold text-[var(--ax-fg)]">로그인</h2>
          <button
            type="button"
            onClick={onClose}
            className="ax-focus-ring rounded-lg p-2 text-[var(--ax-fg)]/60 hover:bg-[var(--ax-border)] hover:text-[var(--ax-fg)]"
            aria-label="닫기"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="mb-2 block text-sm font-medium text-[var(--ax-fg)]">
              이메일
            </label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="ax-focus-ring w-full rounded-lg border border-[var(--ax-border)] bg-[var(--ax-surface)] px-3 py-2 text-[var(--ax-fg)] placeholder-[var(--ax-fg)]/50"
              placeholder="이메일을 입력하세요"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-2 block text-sm font-medium text-[var(--ax-fg)]">
              비밀번호
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="ax-focus-ring w-full rounded-lg border border-[var(--ax-border)] bg-[var(--ax-surface)] px-3 py-2 pr-10 text-[var(--ax-fg)] placeholder-[var(--ax-fg)]/50"
                placeholder="비밀번호를 입력하세요"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="ax-focus-ring absolute right-3 top-1/2 -translate-y-1/2 rounded p-1 text-[var(--ax-fg)]/50 hover:text-[var(--ax-fg)]"
                aria-label={showPassword ? "비밀번호 숨기기" : "비밀번호 보기"}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={isSubmitting || !email || !password}
            className={cn(
              "ax-button-primary ax-focus-ring w-full py-2 text-sm font-medium transition-colors",
              (isSubmitting || !email || !password) && "opacity-50 cursor-not-allowed",
            )}
          >
            {isSubmitting ? "로그인 중..." : "로그인"}
          </button>
        </form>

        <div className="mt-4 text-center text-sm text-[var(--ax-fg)]/70">
          <p>테스트용 계정: 아무 이메일과 비밀번호를 입력하세요</p>
        </div>
      </div>
    </div>
  )
}
