"use client"

import { useState, useMemo } from "react"
import { useSearchParams, useRouter, usePathname } from "next/navigation"
import { mockArticles, mockPapers, mockCommunityPosts } from "@/services/axpress-data"
import type { ArticleCategory } from "@/types/axpress"

export function useArticles() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  const category = (searchParams.get("category") as ArticleCategory) || "all"
  const query = searchParams.get("q") || ""
  const page = Number(searchParams.get("page")) || 1

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const filteredArticles = useMemo(() => {
    let filtered = mockArticles

    if (category !== "all") {
      filtered = filtered.filter((article) => article.category === category)
    }

    if (query) {
      filtered = filtered.filter(
        (article) =>
          article.title.toLowerCase().includes(query.toLowerCase()) ||
          article.summary?.toLowerCase().includes(query.toLowerCase()),
      )
    }

    return filtered
  }, [category, query])

  const updateFilters = (newFilters: { category?: string; q?: string; page?: number }) => {
    const params = new URLSearchParams(searchParams.toString())

    Object.entries(newFilters).forEach(([key, value]) => {
      if (value && value !== "all") {
        params.set(key, value.toString())
      } else {
        params.delete(key)
      }
    })

    router.push(`${pathname}?${params.toString()}`)
  }

  return {
    articles: filteredArticles,
    isLoading,
    error,
    category,
    query,
    page,
    updateFilters,
  }
}

export function usePapers() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  const query = searchParams.get("q") || ""
  const tags = searchParams.get("tags")?.split(",").filter(Boolean) || []
  const from = searchParams.get("from") || ""
  const to = searchParams.get("to") || ""
  const page = Number(searchParams.get("page")) || 1

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const filteredPapers = useMemo(() => {
    let filtered = mockPapers

    if (query) {
      filtered = filtered.filter(
        (paper) =>
          paper.title.toLowerCase().includes(query.toLowerCase()) ||
          paper.abstract.toLowerCase().includes(query.toLowerCase()) ||
          paper.authors.some((author) => author.toLowerCase().includes(query.toLowerCase())),
      )
    }

    return filtered
  }, [query])

  const updateFilters = (newFilters: { q?: string; tags?: string[]; from?: string; to?: string; page?: number }) => {
    const params = new URLSearchParams(searchParams.toString())

    Object.entries(newFilters).forEach(([key, value]) => {
      if (value && (Array.isArray(value) ? value.length > 0 : value !== "")) {
        if (key === "tags" && Array.isArray(value)) {
          params.set(key, value.join(","))
        } else {
          params.set(key, value.toString())
        }
      } else {
        params.delete(key)
      }
    })

    router.push(`${pathname}?${params.toString()}`)
  }

  return {
    papers: filteredPapers,
    isLoading,
    error,
    query,
    tags,
    from,
    to,
    page,
    updateFilters,
  }
}

export function useCommunity() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const pathname = usePathname()

  const query = searchParams.get("q") || ""
  const sort = (searchParams.get("sort") as "recent" | "popular") || "recent"
  const page = Number(searchParams.get("page")) || 1

  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const filteredPosts = useMemo(() => {
    let filtered = mockCommunityPosts

    if (query) {
      filtered = filtered.filter(
        (post) =>
          post.title.toLowerCase().includes(query.toLowerCase()) ||
          post.summary.toLowerCase().includes(query.toLowerCase()),
      )
    }

    if (sort === "popular") {
      filtered = [...filtered].sort((a, b) => b.votes - a.votes)
    } else {
      filtered = [...filtered].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    }

    return filtered
  }, [query, sort])

  const updateFilters = (newFilters: { q?: string; sort?: "recent" | "popular"; page?: number }) => {
    const params = new URLSearchParams(searchParams.toString())

    Object.entries(newFilters).forEach(([key, value]) => {
      if (value && value !== "recent") {
        params.set(key, value.toString())
      } else if (key === "sort" && value === "recent") {
        params.delete(key)
      } else if (!value) {
        params.delete(key)
      }
    })

    router.push(`${pathname}?${params.toString()}`)
  }

  return {
    posts: filteredPosts,
    isLoading,
    error,
    query,
    sort,
    page,
    updateFilters,
  }
}
