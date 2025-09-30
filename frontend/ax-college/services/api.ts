import axios from "axios"

export const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
})

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error?.response?.data?.detail || "문제가 발생했습니다"
    // Note: We can't use hooks in interceptors, so we'll handle errors in components
    console.error("API Error:", message)
    return Promise.reject(error)
  },
)
