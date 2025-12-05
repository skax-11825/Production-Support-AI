import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { TrendingUp, AlertCircle, ArrowRight } from "lucide-react"
import Link from "next/link"

export function AgentNavigation() {
  const agents = [
    {
      icon: TrendingUp,
      title: "State Chase Agent",
      description:
        "실시간 생산•설비 데이터를 기반으로 설비 조회, 작업 우선순위 추천, 원인 분석을 수행하는 제조용 AI 에이전트",
      href: "/state-chase",
      hoverColor: "from-blue-500/20 to-purple-500/20",
      iconGradient: "from-blue-500 to-purple-600",
      shadowColor: "shadow-purple-500/30",
    },
    {
      icon: AlertCircle,
      title: "Error Lense Agent",
      description:
        "장비 에러 및 작업 이력을 통합 분석해 엔지니어에게 즉각적으로 에러 원인 및 조치 방안에 대한 인사이트를 제공하는 AI 에이전트",
      href: "/error-lense",
      hoverColor: "from-orange-500/20 to-red-500/20",
      iconGradient: "from-orange-500 to-red-600",
      shadowColor: "shadow-red-500/30",
    },
  ]

  return (
    <section id="agents" className="border-t border-border/40 bg-secondary/30 py-32">
      <div className="container mx-auto px-6">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-4xl font-semibold tracking-tight sm:text-5xl">AI Agent 선택</h2>
          <p className="mx-auto max-w-2xl text-balance text-lg leading-relaxed text-muted-foreground">
            필요한 AI Agent를 선택하세요. 각 Agent는 특정 제조 과정에 적합하게 설계되었습니다.
          </p>
        </div>

        <div className="mx-auto grid max-w-5xl gap-8 md:grid-cols-2">
          {agents.map((agent, index) => {
            const Icon = agent.icon
            return (
              <Card
                key={index}
                className="group relative overflow-hidden border-border/50 bg-card p-8 transition-all hover:border-accent/50 hover:shadow-2xl hover:shadow-accent/10"
              >
                <div
                  className={`absolute inset-0 bg-gradient-to-br ${agent.hoverColor} opacity-0 transition-opacity group-hover:opacity-100`}
                />

                <div className="relative">
                  <div className={`mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br ${agent.iconGradient} ${agent.shadowColor} shadow-xl transition-transform group-hover:scale-110`}>
                    <Icon className="h-8 w-8 text-white" />
                  </div>

                  <h3 className="mb-4 text-2xl font-semibold">{agent.title}</h3>
                  <p className="mb-6 leading-relaxed text-muted-foreground">{agent.description}</p>

                  <Link href={agent.href}>
                    <Button className="group/btn w-full rounded-full">
                      Agent 시작
                      <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover/btn:translate-x-1" />
                    </Button>
                  </Link>
                </div>
              </Card>
            )
          })}
        </div>
      </div>
    </section>
  )
}
