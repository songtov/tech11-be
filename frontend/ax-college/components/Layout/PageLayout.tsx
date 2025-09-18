import type React from "react"
import { Header } from "@/components/Header/Header"
import { cn } from "@/lib/utils"

interface PageLayoutProps {
  children: React.ReactNode
  className?: string
  maxWidth?: "sm" | "md" | "lg" | "xl" | "2xl" | "full"
}

export function PageLayout({ children, className, maxWidth = "2xl" }: PageLayoutProps) {
  const maxWidthClasses = {
    sm: "max-w-2xl",
    md: "max-w-4xl",
    lg: "max-w-6xl",
    xl: "max-w-7xl",
    "2xl": "max-w-7xl",
    full: "max-w-none",
  }

  return (
    <div className="min-h-screen">
      <Header />
      <main
        className={cn(
          "mx-auto px-4 py-6 md:px-6 md:py-8 lg:px-8 pt-[calc(var(--header-height)+1.5rem)]",
          maxWidthClasses[maxWidth],
          className,
        )}
      >
        {children}
      </main>
    </div>
  )
}
