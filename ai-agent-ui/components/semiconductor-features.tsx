import { Card } from "@/components/ui/card"
import { Database, Server, Brain, User } from "lucide-react"

export function SystemWorkflow() {
  const workflow = [
    {
      icon: Database,
      label: "DB Server",
      description: "Centralized data storage",
      gradient: "from-blue-500 to-cyan-600",
      iconColor: "text-blue-600 dark:text-blue-400",
    },
    {
      icon: Server,
      label: "MCP Server",
      description: "Model Control Protocol",
      gradient: "from-emerald-500 to-teal-600",
      iconColor: "text-emerald-600 dark:text-emerald-400",
    },
    {
      icon: Brain,
      label: "LLM",
      description: "Large Language Model",
      gradient: "from-purple-500 to-pink-600",
      iconColor: "text-purple-600 dark:text-purple-400",
    },
    {
      icon: User,
      label: "Engineer",
      description: "Human oversight",
      gradient: "from-orange-500 to-red-600",
      iconColor: "text-orange-600 dark:text-orange-400",
    },
  ]

  return (
    <section className="container mx-auto px-6 py-32">
      <div className="mb-16 text-center">
        <h2 className="mb-4 text-4xl font-semibold tracking-tight sm:text-5xl">Simplified System Workflow</h2>
        <p className="mx-auto max-w-2xl text-balance text-lg leading-relaxed text-muted-foreground">
          Our AI platform seamlessly integrates data, processing, intelligence, and human expertise.
        </p>
      </div>

      <Card className="mx-auto max-w-5xl border-border/50 bg-gradient-to-br from-card to-card/50 p-12">
        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {workflow.map((step, index) => {
            const Icon = step.icon
            return (
              <div
                key={index}
                className="group relative flex flex-col items-center text-center transition-all hover:scale-105"
              >
                <div
                  className={`mb-4 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br ${step.gradient}/20 border border-${step.gradient.split(" ")[1]}/30 transition-all group-hover:shadow-lg group-hover:shadow-${step.gradient.split(" ")[1]}/30`}
                >
                  <Icon className={`h-10 w-10 ${step.iconColor}`} />
                </div>
                <h3 className="mb-2 text-base font-bold">{step.label}</h3>
                <p className="text-xs text-muted-foreground">{step.description}</p>
                {index < workflow.length - 1 && (
                  <div className="absolute -right-4 top-10 hidden text-muted-foreground/30 lg:block">→</div>
                )}
              </div>
            )
          })}
        </div>
      </Card>
    </section>
  )
}
