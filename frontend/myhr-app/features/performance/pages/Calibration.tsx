"use client"

import { useState } from "react"
import { BarChart3, Users, Settings, Save } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Slider } from "@/components/ui/slider"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts"
import PageContainer from "@/components/layout/PageContainer"

const mockDistributionData = [
  { range: "1.0-1.5", count: 2, percentage: 5 },
  { range: "1.5-2.0", count: 3, percentage: 8 },
  { range: "2.0-2.5", count: 5, percentage: 13 },
  { range: "2.5-3.0", count: 8, percentage: 21 },
  { range: "3.0-3.5", count: 12, percentage: 32 },
  { range: "3.5-4.0", count: 6, percentage: 16 },
  { range: "4.0-4.5", count: 2, percentage: 5 },
  { range: "4.5-5.0", count: 0, percentage: 0 },
]

export default function Calibration() {
  const [selectedOrg, setSelectedOrg] = useState("dev-team")
  const [topPerformers, setTopPerformers] = useState([10])
  const [bottomPerformers, setBottomPerformers] = useState([10])

  const handleSaveCalibration = () => {
    console.log("[v0] Saving calibration settings:", {
      organization: selectedOrg,
      topPerformersPercent: topPerformers[0],
      bottomPerformersPercent: bottomPerformers[0],
    })
    // Here you would typically save to the backend
  }

  return (
    <PageContainer title="성과 보정">
      <div className="space-y-6">
        {/* Organization Selection */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              조직 선택
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-4">
              <Select value={selectedOrg} onValueChange={setSelectedOrg}>
                <SelectTrigger className="w-64">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="dev-team">개발팀</SelectItem>
                  <SelectItem value="marketing-team">마케팅팀</SelectItem>
                  <SelectItem value="sales-team">영업팀</SelectItem>
                  <SelectItem value="hr-team">인사팀</SelectItem>
                </SelectContent>
              </Select>

              <div className="text-sm text-muted-foreground">총 38명의 직원</div>
            </div>
          </CardContent>
        </Card>

        {/* Distribution Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              성과 점수 분포
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={mockDistributionData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                  <XAxis dataKey="range" stroke="var(--muted-foreground)" fontSize={12} />
                  <YAxis stroke="var(--muted-foreground)" fontSize={12} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "var(--background)",
                      border: "1px solid var(--border)",
                      borderRadius: "8px",
                      color: "var(--foreground)",
                    }}
                    formatter={(value, name) => [
                      `${value}명 (${mockDistributionData.find((d) => d.count === value)?.percentage}%)`,
                      "직원 수",
                    ]}
                  />
                  <Bar dataKey="count" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Calibration Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings className="h-5 w-5" />
              보정 설정
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Top Performers */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <label className="text-sm font-medium">상위 성과자 비율</label>
                <span className="text-sm text-muted-foreground">{topPerformers[0]}%</span>
              </div>
              <Slider
                value={topPerformers}
                onValueChange={setTopPerformers}
                max={30}
                min={5}
                step={1}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground mt-2">4.0점 이상 받을 수 있는 직원의 최대 비율</p>
            </div>

            {/* Bottom Performers */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <label className="text-sm font-medium">하위 성과자 비율</label>
                <span className="text-sm text-muted-foreground">{bottomPerformers[0]}%</span>
              </div>
              <Slider
                value={bottomPerformers}
                onValueChange={setBottomPerformers}
                max={20}
                min={5}
                step={1}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground mt-2">2.0점 이하 받아야 하는 직원의 최소 비율</p>
            </div>

            {/* Impact Summary */}
            <div className="bg-muted/50 p-4 rounded-lg">
              <h4 className="font-medium mb-2">보정 영향</h4>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">상위 성과자:</span>
                  <span className="ml-2 font-medium">최대 {Math.round((38 * topPerformers[0]) / 100)}명</span>
                </div>
                <div>
                  <span className="text-muted-foreground">하위 성과자:</span>
                  <span className="ml-2 font-medium">최소 {Math.round((38 * bottomPerformers[0]) / 100)}명</span>
                </div>
              </div>
            </div>

            {/* Save Button */}
            <div className="flex justify-end">
              <Button onClick={handleSaveCalibration}>
                <Save className="h-4 w-4 mr-2" />
                보정 설정 저장
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
