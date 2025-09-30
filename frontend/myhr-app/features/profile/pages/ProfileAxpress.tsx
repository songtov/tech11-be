"use client";

import { useMemo, useState, useEffect } from "react";
import { BookOpenCheck, Brain, Clock, Download, Loader2, Search, Settings, Sparkles, Star, Target, BellRing, Link as LinkIcon, ShieldCheck, Zap } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Progress } from "@/components/ui/progress";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import PageContainer from "@/components/layout/PageContainer";
import { ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from "recharts";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

// NOTE: 핵심 육각형(레이더) 비주얼은 유지. 색/레이아웃만 최소 조정.
export default function AxpressPapersDashboard() {
  const [selectedRound, setSelectedRound] = useState("2024-Q3");
  const [isAxpressLinked, setIsAxpressLinked] = useState(true); // 자동 연동 기본 ON
  const [domain, setDomain] = useState("all");
  const [range, setRange] = useState("30d");
  const [loading, setLoading] = useState(false);
  const [triageFilter, setTriageFilter] = useState("all");

  // Mock: 레이더 데이터 (육각형 최대한 유지)
  const radarData = useMemo(() => ([
    { subject: "제조", A: 4.2, fullMark: 5 },
    { subject: "유통/물류", A: 3.8, fullMark: 5 },
    { subject: "금융", A: 4.5, fullMark: 5 },
    { subject: "통신", A: 4.0, fullMark: 5 },
    { subject: "생성형AI", A: 3.6, fullMark: 5 },
    { subject: "Cloud", A: 4.1, fullMark: 5 },
  ]), []);

  // Mock KPIs
  const kpis = useMemo(() => ([
    { icon: <Sparkles className="h-4 w-4" />, label: "신규 논문 발견", value: 42, sub: "최근 30일" },
    { icon: <BookOpenCheck className="h-4 w-4" />, label: "리딩 완료", value: 18, sub: "요약+하이라이트 저장" },
    { icon: <Brain className="h-4 w-4" />, label: "이해도 지표", value: 86, sub: "퀴즈/요점 회상" },
    { icon: <Clock className="h-4 w-4" />, label: "절약 시간", value: "12.4h", sub: "자동 요약/태깅" },
  ]), []);

  // Skeleton 로딩 시뮬레이션 (API 연동 위치)
  useEffect(() => {
    setLoading(true);
    const t = setTimeout(() => setLoading(false), 600);
    return () => clearTimeout(t);
  }, [selectedRound, domain, range, triageFilter]);

  return (
    <PageContainer title="AXpress profile">
      {/* 상단 컨트롤 바 */}
      <div className="sticky top-0 z-10 -mx-4 px-4 py-3 bg-background/80 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-2">
            <Tabs value={selectedRound} onValueChange={setSelectedRound} className="w-full">
              <TabsList className="grid grid-cols-4 w-full md:w-auto">
                <TabsTrigger value="2024-Q1">2024 Q1</TabsTrigger>
                <TabsTrigger value="2024-Q2">2024 Q2</TabsTrigger>
                <TabsTrigger value="2024-Q3">2024 Q3</TabsTrigger>
                <TabsTrigger value="2024-Q4">2024 Q4</TabsTrigger>
              </TabsList>
            </Tabs>
            <Badge variant="secondary" className="ml-2">조회 전용 - 편집 불가</Badge>
          </div>

          <div className="flex items-center gap-2">
            <Select value={domain} onValueChange={setDomain}>
              <SelectTrigger className="w-40"><SelectValue placeholder="도메인"/></SelectTrigger>
              <SelectContent>
                <SelectItem value="all">전체 도메인</SelectItem>
                <SelectItem value="ai">생성형AI</SelectItem>
                <SelectItem value="cloud">Cloud</SelectItem>
                <SelectItem value="finance">금융</SelectItem>
                <SelectItem value="manufacturing">제조</SelectItem>
                <SelectItem value="telco">통신</SelectItem>
                <SelectItem value="logistics">유통/물류</SelectItem>
              </SelectContent>
            </Select>
            <Select value={range} onValueChange={setRange}>
              <SelectTrigger className="w-32"><SelectValue placeholder="기간"/></SelectTrigger>
              <SelectContent>
                <SelectItem value="7d">7일</SelectItem>
                <SelectItem value="30d">30일</SelectItem>
                <SelectItem value="90d">90일</SelectItem>
              </SelectContent>
            </Select>
            <div className="relative w-64 hidden md:block">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input className="pl-8" placeholder="키워드, 저자, 학회…" aria-label="검색"/>
            </div>
            <Button variant="outline" size="icon" aria-label="설정"><Settings className="h-4 w-4"/></Button>
          </div>
        </div>
      </div>

      {/* KPI 카드 */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mt-4">
        {kpis.map((k, i) => (
          <Card key={i} className="hover:shadow-md transition-shadow">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base font-semibold flex items-center gap-2">{k.icon}{k.label}</CardTitle>
                <Badge variant="outline">{k.sub}</Badge>
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{k.value}</div>
              {k.label === "이해도 지표" && <Progress value={Number(k.value)} className="mt-3"/>}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 핵심 역량(육각형) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Target className="h-5 w-5 text-[var(--primary)]"/>핵심 역량 분석</CardTitle>
            <CardDescription>도메인별 리서치 역량을 5점 만점으로 표준화</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
                <PolarRadiusAxis angle={90} domain={[0, 5]} tick={{ fontSize: 10 }} />
                <Radar name="점수" dataKey="A" stroke="#5277F1" fill="#5277F1" fillOpacity={0.25} strokeWidth={2} />
              </RadarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Triage & Queue */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Zap className="h-5 w-5 text-[var(--primary)]"/>원클릭 트리아지</CardTitle>
            <CardDescription>자동 요약·품질점수로 읽기 우선순위 정렬 </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center gap-2">
              <Label className="text-sm text-muted-foreground">필터</Label>
              <Select value={triageFilter} onValueChange={setTriageFilter}>
                <SelectTrigger className="w-32"><SelectValue placeholder="상태"/></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">전체</SelectItem>
                  <SelectItem value="new">신규</SelectItem>
                  <SelectItem value="queued">찜 목록</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="grid gap-2">
              {loading ? (
                <div className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin"/>추천 로딩…</div>
              ) : (
                [1,2,3].map((i) => (
                  <div key={i} className="group flex items-center justify-between rounded-xl border p-3 hover:bg-accent/30">
                    <div>
                      <div className="font-medium">[CVPR'25] Token-efficient Diffusion via XYZ</div>
                      <div className="text-xs text-muted-foreground">품질 91 · 인용 예측 상위 10% · 요약 3줄</div>
                    </div>
                    <div className="flex items-center gap-2 opacity-100 md:opacity-0 md:group-hover:opacity-100 transition-opacity">
                      <Button size="sm" variant="secondary" aria-label="읽기 큐에 추가">Add</Button>
                      <Button size="sm" variant="ghost" aria-label="세부">Details</Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 리딩 효과 & 회상 테스트 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mt-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Brain className="h-5 w-5 text-[var(--primary)]"/>리딩 효과 측정</CardTitle>
            <CardDescription>핵심 문장 회상·퀴즈·적용사례 기록 기반</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Metric label="퀴즈 정답률" value={86} suffix="%"/>
              <Metric label="요점 회상" value={4.3} suffix="/5"/>
              <Metric label="적용 메모" value={27} suffix="건"/>
            </div>
            <Separator/>
            <div className="text-sm text-muted-foreground">* 논문별 자동 생성되는 퀴즈와 논문 로그로 측정합니다.</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Star className="h-5 w-5 text-[var(--primary)]"/>임팩트 점수</CardTitle>
            <CardDescription>사내 구성원 평균치에 비한 상대 점수</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {(() => {
              const impactItems = [
                { label: "공유/반응", score: 74, detail: "공유 52회 · 반응 22건" },
                { label: "프로토타입 연결", score: 45, detail: "연결 9건 · 시도 20회" },
                { label: "사내 참고문서 인용", score: 60, detail: "인용 13건" },
              ];
              return (
                <TooltipProvider>
                  {impactItems.map((item, idx) => (
                    <div key={idx} className="space-y-3">
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <div className="flex items-center justify-between cursor-help">
                            <div className="text-sm">{item.label}</div>
                            <div className="font-semibold">{item.score}</div>
                          </div>
                        </TooltipTrigger>
                        <TooltipContent>
                          <p>{item.detail}</p>
                        </TooltipContent>
                      </Tooltip>
                      <Progress value={item.score}/>
                    </div>
                  ))}
                </TooltipProvider>
              );
            })()}
          </CardContent>
        </Card>
      </div>

      {/* AXPress 연동 (Zero-config) */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2"><LinkIcon className="h-5 w-5 text-[var(--primary)]"/>AXPress 자동 등록</CardTitle>
          <CardDescription>MyHR 계정 연동만으로 논문 자동 수집·동기화</CardDescription>
        </CardHeader>
        <CardContent className="space-y-5">
          <div className="flex items-center justify-between rounded-xl border p-3">
            <div>
              <div className="font-medium flex items-center gap-2">
                <ShieldCheck className="h-4 w-4"/>연동 상태 {isAxpressLinked ? <Badge variant="secondary">활성</Badge> : <Badge variant="destructive">해제</Badge>}
              </div>
              <p className="text-sm text-muted-foreground mt-1"> 접근 범위 : CareerPath, 성과관리, MyProfile, AXCollege</p>
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={isAxpressLinked} onCheckedChange={setIsAxpressLinked} aria-label="AXPress 연동 토글"/>             
            </div>
          </div>
         
        </CardContent>
      </Card>      
    </PageContainer>
  );
}

function Metric({ label, value, suffix }: { label: string; value: number | string; suffix?: string }) {
  return (
    <Card className="border-dashed">
      <CardHeader className="pb-2"><CardDescription>{label}</CardDescription></CardHeader>
      <CardContent className="pt-0">
        <div className="text-2xl font-bold">{value}{suffix ? <span className="text-base font-normal ml-1 text-muted-foreground">{suffix}</span> : null}</div>
      </CardContent>
    </Card>
  );
}

function AutoRule({ title, desc }: { title: string; desc: string }) {
  return (
    <div className="rounded-xl border p-3">
      <div className="font-medium">{title}</div>
      <div className="text-sm text-muted-foreground">{desc}</div>
    </div>
  );
}