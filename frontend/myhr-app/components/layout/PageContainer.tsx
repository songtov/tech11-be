import type React from "react"
interface PageContainerProps {
  title?: string
  children: React.ReactNode
}

export default function PageContainer({ title, children }: PageContainerProps) {
  return (
    <div className="flex-1 p-6">
      {title && (
        <div className="mb-6">
          <h1 className="text-2xl font-semibold text-foreground">{title}</h1>
        </div>
      )}
      {children}
    </div>
  )
}
