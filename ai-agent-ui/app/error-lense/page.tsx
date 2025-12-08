import { Header } from "@/components/header"
import { ChatInterface } from "@/components/chat-interface"
import { Card } from "@/components/ui/card"
import { Search, ShieldCheck, Lightbulb } from "lucide-react"

export default function ErrorLensePage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-secondary/20">
      <Header />
      <div className="container mx-auto px-6 pt-32 pb-16">
        <div className="mb-16 text-center">
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-orange-500 to-red-600 shadow-xl shadow-red-500/30">
            <Search className="h-10 w-10 text-white" />
          </div>
          <h1 className="mb-4 text-5xl font-semibold tracking-tight sm:text-6xl">Error Lens Agent</h1>
          <p className="mx-auto max-w-2xl text-balance text-lg leading-relaxed text-muted-foreground">
            장비 에러 및 작업 이력을 통합 분석해 엔지니어에게 즉각적으로 에러 원인 및 조치 방안에 대한 인사이트를 제공하는 AI 에이전트
          </p>
        </div>

        <div className="mb-16 grid gap-6 md:grid-cols-3">
          <Card className="border-border/50 bg-card/50 p-6 backdrop-blur-sm transition-all hover:shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-orange-500/20 to-red-500/20">
              <Search className="h-5 w-5 text-orange-600 dark:text-orange-400" />
            </div>
            <h3 className="mb-2 font-semibold">데이터 집계 및 랭킹</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
            기간, 장비, 공정, 에러 코드를 기준으로 건수, 다운타임, 순위 등을 정량적으로 조회합니다.
            </p>
          </Card>

          <Card className="border-border/50 bg-card/50 p-6 backdrop-blur-sm transition-all hover:shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500/20 to-teal-500/20">
              <ShieldCheck className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <h3 className="mb-2 font-semibold">심층 분석 및 지식 검색</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
            과거 이력, 조치 매뉴얼, 유사 사례, 원인 분석 등 맥락을 이용해 질의응답을 진행합니다.
            </p>
          </Card>

          <Card className="border-border/50 bg-card/50 p-6 backdrop-blur-sm transition-all hover:shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20">
              <Lightbulb className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <h3 className="mb-2 font-semibold">복합 및 기타 질문</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              집계 + 상세 검색 결과를 조합해 복합 질의응답을 진행합니다.
            </p>
          </Card>
        </div>

        <ChatInterface agentType="error-lense" />
      </div>
    </main>
  )
}
