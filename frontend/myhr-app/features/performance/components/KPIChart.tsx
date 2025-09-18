"use client"

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"

interface KPIChartProps {
  data: Array<{
    month: string
    goals: number
    reviews: number
    feedback: number
  }>
}

export default function KPIChart({ data }: KPIChartProps) {
  return (
    <div className="h-80">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis dataKey="month" stroke="var(--muted-foreground)" fontSize={12} />
          <YAxis stroke="var(--muted-foreground)" fontSize={12} />
          <Tooltip
            contentStyle={{
              backgroundColor: "var(--background)",
              border: "1px solid var(--border)",
              borderRadius: "8px",
              color: "var(--foreground)",
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="goals"
            stroke="var(--primary)"
            strokeWidth={2}
            name="목표 달성률"
            dot={{ fill: "var(--primary)", strokeWidth: 2, r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="reviews"
            stroke="var(--accent)"
            strokeWidth={2}
            name="평가 점수"
            dot={{ fill: "var(--accent)", strokeWidth: 2, r: 4 }}
          />
          <Line
            type="monotone"
            dataKey="feedback"
            stroke="var(--success)"
            strokeWidth={2}
            name="피드백 점수"
            dot={{ fill: "var(--success)", strokeWidth: 2, r: 4 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
