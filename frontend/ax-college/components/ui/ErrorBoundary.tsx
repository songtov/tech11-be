"use client"

import type React from "react"
import { Component, type ReactNode } from "react"
import { EmptyState } from "./EmptyState"

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error?: Error
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <EmptyState
          title="오류가 발생했습니다"
          description="페이지를 불러오는 중 문제가 발생했습니다. 새로고침 후 다시 시도해주세요."
          action={{ label: "홈으로", href: "/" }}
        />
      )
    }

    return this.props.children
  }
}
