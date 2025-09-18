"use client"

import { create } from "zustand"

export interface KPI {
  name: string
  current: number
  target: number
  unit: string
}

export interface KeyResult {
  id: string
  title: string
  progress: number
  target: number
  current: number
  unit: string
}

export interface Goal {
  id: string
  title: string
  description: string
  ownerId: string
  ownerName: string
  progress: number
  dueDate: string
  status: "idle" | "in-progress" | "completed" | "delayed" | "at_risk" | "overdue"
  priority: "high" | "medium" | "low"
  category: string
  kpis: KPI[]
  keyResults?: KeyResult[]
  createdAt: string
  updatedAt: string
}

export interface Review {
  id: string
  round: string
  title: string
  status: "idle" | "draft" | "submitted" | "needs_changes" | "approved"
  score?: number
  dueDate: string
  createdAt: string
  updatedAt: string
}

export interface Feedback {
  id: string
  fromId: string
  fromName: string
  toId: string
  toName: string
  title: string
  content: string
  type: "positive" | "constructive" | "request"
  read: boolean
  createdAt: string
}

interface PerformanceState {
  // Data
  goals: Goal[]
  reviews: Review[]
  feedbacks: Feedback[]

  // Loading states
  isLoadingGoals: boolean
  isLoadingReviews: boolean
  isLoadingFeedbacks: boolean

  // Filters
  goalFilters: {
    year: string
    quarter: string
    status: string
  }

  // Actions
  setGoals: (goals: Goal[]) => void
  setReviews: (reviews: Review[]) => void
  setFeedbacks: (feedbacks: Feedback[]) => void
  setGoalFilters: (filters: Partial<PerformanceState["goalFilters"]>) => void

  // CRUD operations
  addGoal: (goal: Omit<Goal, "id" | "createdAt" | "updatedAt">) => void
  updateGoal: (id: string, updates: Partial<Goal>) => void
  deleteGoal: (id: string) => void

  addReview: (review: Omit<Review, "id" | "createdAt" | "updatedAt">) => void
  updateReview: (id: string, updates: Partial<Review>) => void

  addFeedback: (feedback: Omit<Feedback, "id" | "createdAt">) => void
  markFeedbackAsRead: (id: string) => void
}

export const usePerformanceStore = create<PerformanceState>((set, get) => ({
  // Initial state
  goals: [
    {
      id: "1",
      title: "Q2 매출 목표 달성",
      description: "2분기 개인 매출 목표 1억원 달성하여 팀 전체 목표에 기여",
      ownerId: "user1",
      ownerName: "김직원",
      progress: 75,
      dueDate: "2024-06-30",
      status: "in-progress",
      priority: "high",
      category: "매출",
      kpis: [
        { name: "매출액", current: 75000000, target: 100000000, unit: "원" },
        { name: "신규 고객", current: 12, target: 15, unit: "명" },
      ],
      keyResults: [
        {
          id: "kr1",
          title: "신규 고객 15명 확보",
          progress: 80,
          target: 15,
          current: 12,
          unit: "명",
        },
        {
          id: "kr2",
          title: "기존 고객 매출 20% 증가",
          progress: 70,
          target: 20,
          current: 14,
          unit: "%",
        },
        {
          id: "kr3",
          title: "월평균 매출 3,300만원 달성",
          progress: 75,
          target: 33000000,
          current: 25000000,
          unit: "원",
        },
      ],
      createdAt: "2024-01-01T00:00:00Z",
      updatedAt: "2024-03-15T10:00:00Z",
    },
    {
      id: "2",
      title: "팀 프로젝트 완료",
      description: "신규 HR 시스템 개발 프로젝트를 품질 기준에 맞춰 완료",
      ownerId: "user1",
      ownerName: "김직원",
      progress: 90,
      dueDate: "2024-05-15",
      status: "in-progress",
      priority: "high",
      category: "프로젝트",
      kpis: [
        { name: "진행률", current: 90, target: 100, unit: "%" },
        { name: "품질 점수", current: 85, target: 90, unit: "점" },
      ],
      keyResults: [
        {
          id: "kr4",
          title: "핵심 기능 개발 완료",
          progress: 95,
          target: 100,
          current: 95,
          unit: "%",
        },
        {
          id: "kr5",
          title: "테스트 커버리지 90% 달성",
          progress: 85,
          target: 90,
          current: 85,
          unit: "%",
        },
        {
          id: "kr6",
          title: "사용자 만족도 4.5점 이상",
          progress: 88,
          target: 4.5,
          current: 4.4,
          unit: "점",
        },
      ],
      createdAt: "2024-02-01T00:00:00Z",
      updatedAt: "2024-03-14T15:30:00Z",
    },
  ],

  reviews: [
    {
      id: "1",
      round: "2024-Q1",
      title: "1분기 성과 평가",
      status: "submitted",
      score: 4.2,
      dueDate: "2024-04-15",
      createdAt: "2024-03-01T00:00:00Z",
      updatedAt: "2024-03-10T14:20:00Z",
    },
    {
      id: "2",
      round: "2024-Q2",
      title: "2분기 성과 평가",
      status: "draft",
      dueDate: "2024-07-15",
      createdAt: "2024-06-01T00:00:00Z",
      updatedAt: "2024-06-01T00:00:00Z",
    },
  ],

  feedbacks: [
    {
      id: "1",
      fromId: "manager1",
      fromName: "박팀장",
      toId: "user1",
      toName: "김직원",
      title: "프로젝트 진행 관련 피드백",
      content: "프로젝트 진행 상황이 매우 좋습니다. 계속 이런 식으로 진행해주세요.",
      type: "positive",
      read: false,
      createdAt: "2024-03-14T09:30:00Z",
    },
    {
      id: "2",
      fromId: "user1",
      fromName: "김직원",
      toId: "colleague1",
      toName: "이동료",
      title: "협업 관련 감사 인사",
      content: "지난 프로젝트에서 많은 도움을 주셔서 감사합니다.",
      type: "positive",
      read: true,
      createdAt: "2024-03-13T16:45:00Z",
    },
  ],

  isLoadingGoals: false,
  isLoadingReviews: false,
  isLoadingFeedbacks: false,

  goalFilters: {
    year: "2024",
    quarter: "Q2",
    status: "all",
  },

  // Setters
  setGoals: (goals) => set({ goals }),
  setReviews: (reviews) => set({ reviews }),
  setFeedbacks: (feedbacks) => set({ feedbacks }),
  setGoalFilters: (filters) =>
    set((state) => ({
      goalFilters: { ...state.goalFilters, ...filters },
    })),

  // CRUD operations
  addGoal: (goalData) => {
    const newGoal: Goal = {
      ...goalData,
      id: Date.now().toString(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
    set((state) => ({ goals: [newGoal, ...state.goals] }))
  },

  updateGoal: (id, updates) => {
    set((state) => ({
      goals: state.goals.map((goal) =>
        goal.id === id ? { ...goal, ...updates, updatedAt: new Date().toISOString() } : goal,
      ),
    }))
  },

  deleteGoal: (id) => {
    set((state) => ({
      goals: state.goals.filter((goal) => goal.id !== id),
    }))
  },

  addReview: (reviewData) => {
    const newReview: Review = {
      ...reviewData,
      id: Date.now().toString(),
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
    set((state) => ({ reviews: [newReview, ...state.reviews] }))
  },

  updateReview: (id, updates) => {
    set((state) => ({
      reviews: state.reviews.map((review) =>
        review.id === id ? { ...review, ...updates, updatedAt: new Date().toISOString() } : review,
      ),
    }))
  },

  addFeedback: (feedbackData) => {
    const newFeedback: Feedback = {
      ...feedbackData,
      id: Date.now().toString(),
      createdAt: new Date().toISOString(),
    }
    set((state) => ({ feedbacks: [newFeedback, ...state.feedbacks] }))
  },

  markFeedbackAsRead: (id) => {
    set((state) => ({
      feedbacks: state.feedbacks.map((feedback) => (feedback.id === id ? { ...feedback, read: true } : feedback)),
    }))
  },
}))
