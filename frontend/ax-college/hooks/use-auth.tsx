"use client"

import type React from "react"

import { useState, useEffect, createContext, useContext } from "react"
import { useRouter } from "next/navigation"
import { useAXToast } from "./use-toast"

interface User {
  id: string
  name: string
  email: string
  role: "student" | "instructor" | "admin"
}

interface AuthContextType {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const { showLoginRequiredToast } = useAXToast()
  const router = useRouter()

  // Mock authentication - in real app, this would check with server
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Simulate API call delay
        await new Promise((resolve) => setTimeout(resolve, 1000))

        // Check if user is logged in (mock implementation)
        const savedUser = localStorage.getItem("ax-college-user")
        if (savedUser) {
          setUser(JSON.parse(savedUser))
        }
      } catch (error) {
        console.error("Auth check failed:", error)
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    setIsLoading(true)
    try {
      // Mock login API call
      await new Promise((resolve) => setTimeout(resolve, 1000))

      // Mock user data
      const mockUser: User = {
        id: "1",
        name: "김학습",
        email: email,
        role: "student",
      }

      setUser(mockUser)
      localStorage.setItem("ax-college-user", JSON.stringify(mockUser))
    } catch (error) {
      throw new Error("로그인에 실패했습니다.")
    } finally {
      setIsLoading(false)
    }
  }

  const logout = () => {
    setUser(null)
    localStorage.removeItem("ax-college-user")
    router.push("/")
  }

  const value: AuthContextType = {
    user,
    isLoading,
    login,
    logout,
    isAuthenticated: !!user,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useRequireAuth() {
  const { isAuthenticated, isLoading } = useAuth()
  const { showLoginRequiredToast } = useAXToast()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      showLoginRequiredToast()
      router.push("/")
    }
  }, [isAuthenticated, isLoading, showLoginRequiredToast, router])

  return { isAuthenticated, isLoading }
}
