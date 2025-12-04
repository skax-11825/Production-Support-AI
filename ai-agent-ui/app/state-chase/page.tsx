import { Header } from "@/components/header"
import { ChatInterface } from "@/components/chat-interface"
import { Card } from "@/components/ui/card"
import { TrendingUp, Target, BarChart3, Zap } from "lucide-react"

export default function StateChaseAgentPage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-secondary/20">
      <Header />
      <div className="container mx-auto px-6 pt-32 pb-16">
        <div className="mb-16 text-center">
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-blue-500 to-purple-600 shadow-xl shadow-purple-500/30">
            <TrendingUp className="h-10 w-10 text-white" />
          </div>
          <h1 className="mb-4 text-5xl font-semibold tracking-tight sm:text-6xl">State Chase Agent</h1>
          <p className="mx-auto max-w-2xl text-balance text-lg leading-relaxed text-muted-foreground">
            AI-powered production scheduling and resource optimization for semiconductor manufacturing
          </p>
        </div>

        <div className="mb-16 grid gap-6 md:grid-cols-3">
          <Card className="border-border/50 bg-card/50 p-6 backdrop-blur-sm transition-all hover:shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-500/20">
              <Target className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="mb-2 font-semibold">Smart Scheduling</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Optimize production schedules with AI-driven resource allocation
            </p>
          </Card>

          <Card className="border-border/50 bg-card/50 p-6 backdrop-blur-sm transition-all hover:shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500/20 to-teal-500/20">
              <BarChart3 className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <h3 className="mb-2 font-semibold">Real-time Analytics</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Monitor production states and identify bottlenecks instantly
            </p>
          </Card>

          <Card className="border-border/50 bg-card/50 p-6 backdrop-blur-sm transition-all hover:shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20">
              <Zap className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <h3 className="mb-2 font-semibold">Predictive Insights</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Forecast production delays and optimize resource utilization
            </p>
          </Card>
        </div>

        <ChatInterface agentType="state-chase" />
      </div>
    </main>
  )
}
