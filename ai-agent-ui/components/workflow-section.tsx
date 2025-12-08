import { Card } from "@/components/ui/card"

export function WorkflowSection() {
  const workflows = [
    {
      step: "01",
      title: "Error Detection",
      description: "System monitors logs and identifies anomalies using pattern recognition and ML models",
    },
    {
      step: "02",
      title: "Context Analysis",
      description: "AI agent gathers relevant context from knowledge base and historical data",
    },
    {
      step: "03",
      title: "Solution Generation",
      description: "Dify workflow processes information and generates actionable solutions",
    },
    {
      step: "04",
      title: "Automated Resolution",
      description: "System applies fixes automatically or provides clear guidance to engineers",
    },
  ]

  return (
    <section id="workflow" className="container mx-auto px-6 py-32">
      <div className="mb-16 text-center">
        <h2 className="mb-4 text-4xl font-semibold tracking-tight sm:text-5xl">Intelligent Workflow</h2>
        <p className="mx-auto max-w-2xl text-balance text-lg leading-relaxed text-muted-foreground">
          Error Lens uses a sophisticated multi-step workflow powered by Dify to detect, analyze, and resolve errors
          automatically.
        </p>
      </div>

      <div className="mx-auto max-w-4xl space-y-6">
        {workflows.map((workflow, index) => (
          <Card
            key={index}
            className="group overflow-hidden border-border/50 bg-card p-8 transition-all hover:border-accent/50 hover:shadow-lg hover:shadow-accent/5"
          >
            <div className="flex items-start gap-6">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-accent/10 text-xl font-bold text-accent transition-colors group-hover:bg-accent group-hover:text-accent-foreground">
                {workflow.step}
              </div>
              <div className="flex-1">
                <h3 className="mb-2 text-xl font-semibold">{workflow.title}</h3>
                <p className="leading-relaxed text-muted-foreground">{workflow.description}</p>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </section>
  )
}
