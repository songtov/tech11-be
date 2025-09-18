import type React from "react"
import type { Metadata } from "next"
import { GeistSans } from "geist/font/sans"
import { GeistMono } from "geist/font/mono"
import { Analytics } from "@vercel/analytics/next"
import { Suspense } from "react"
import "./globals.css"
import Header from "@/components/layout/Header"
import LeftSidebar from "@/components/layout/LeftSidebar/LeftSidebar"

export const metadata: Metadata = {
  title: "MyHR - 인사관리 시스템",
  description: "MyHR 기업 인사관리 시스템",
  generator: "v0.app",
  icons: { icon: "/logo-skax.ico" },
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="ko">
      <body className={`font-sans ${GeistSans.variable} ${GeistMono.variable}`}>
        <div className="flex h-screen bg-background">
          <Suspense fallback={<div>Loading...</div>}>
            <LeftSidebar />
            <div className="flex-1 flex flex-col">
              <Header />
              <main className="flex-1 overflow-auto">{children}</main>
            </div>
          </Suspense>
        </div>
        <Analytics />
      </body>
    </html>
  )
}
