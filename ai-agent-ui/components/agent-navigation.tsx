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
        "Optimize production scheduling with AI-powered lot planning and resource allocation for maximum efficiency.",
      href: "/state-chase",
      color: "from-blue-500/20 to-cyan-500/20",
    },
    {
      icon: AlertCircle,
      title: "Error Lense",
      description:
        "Real-time error detection and resolution with intelligent root cause analysis and automated troubleshooting.",
      href: "/error-lense",
      color: "from-orange-500/20 to-red-500/20",
    },
  ]

  return (
    <section id="agents" className="border-t border-border/40 bg-secondary/30 py-32">
      <div className="container mx-auto px-6">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-4xl font-semibold tracking-tight sm:text-5xl">Choose Your AI Agent</h2>
          <p className="mx-auto max-w-2xl text-balance text-lg leading-relaxed text-muted-foreground">
            Select an AI agent to assist with your production needs. Each agent is specialized for specific
            manufacturing challenges.
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
                  className={`absolute inset-0 bg-gradient-to-br ${agent.color} opacity-0 transition-opacity group-hover:opacity-100`}
                />

                <div className="relative">
                  <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-accent text-accent-foreground transition-transform group-hover:scale-110">
                    <Icon className="h-8 w-8" />
                  </div>

                  <h3 className="mb-4 text-2xl font-semibold">{agent.title}</h3>
                  <p className="mb-6 leading-relaxed text-muted-foreground">{agent.description}</p>

                  <Link href={agent.href}>
                    <Button className="group/btn w-full rounded-full">
                      Launch Agent
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
