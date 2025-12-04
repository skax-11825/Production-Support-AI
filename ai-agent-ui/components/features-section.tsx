import { Card } from "@/components/ui/card"
import { Cpu, Gauge, LineChart, Microscope, Shield, Workflow, Zap, CircuitBoard } from "lucide-react"

export function FeaturesSection() {
  const features = [
    {
      icon: CircuitBoard,
      title: "Wafer Defect Detection",
      description:
        "Real-time AI analysis of wafer fabrication processes to identify micro-defects and pattern anomalies before they impact yield.",
    },
    {
      icon: Microscope,
      title: "Process Monitoring",
      description:
        "Continuous monitoring of photolithography, etching, and deposition processes with instant anomaly detection.",
    },
    {
      icon: Gauge,
      title: "Equipment Health Tracking",
      description:
        "Predictive maintenance for semiconductor manufacturing equipment, reducing downtime and optimizing production schedules.",
    },
    {
      icon: LineChart,
      title: "Yield Optimization",
      description:
        "Advanced analytics that correlate process parameters with yield outcomes to maximize production efficiency.",
    },
    {
      icon: Zap,
      title: "Real-time Error Analysis",
      description:
        "Sub-millisecond error detection across all fabrication stages with automated root cause analysis and resolution suggestions.",
    },
    {
      icon: Shield,
      title: "Quality Assurance",
      description:
        "Automated quality control checks at every manufacturing step, ensuring compliance with SK Group standards.",
    },
    {
      icon: Cpu,
      title: "Smart Factory Integration",
      description: "Seamless integration with existing MES and ERP systems for unified manufacturing intelligence.",
    },
    {
      icon: Workflow,
      title: "Process Optimization",
      description:
        "AI-driven recommendations for process parameter adjustments to improve throughput and reduce waste.",
    },
  ]

  return (
    <section id="features" className="container mx-auto px-6 py-32">
      <div className="mb-16 text-center">
        <h2 className="mb-4 text-4xl font-semibold tracking-tight sm:text-5xl">
          Semiconductor Manufacturing Intelligence
        </h2>
        <p className="mx-auto max-w-2xl text-balance text-lg leading-relaxed text-muted-foreground">
          Enterprise-grade agentic AI platform designed specifically for SK Group's semiconductor manufacturing
          operations.
        </p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {features.map((feature, index) => {
          const Icon = feature.icon
          return (
            <Card
              key={index}
              className="group relative overflow-hidden border-border/50 bg-card p-6 transition-all hover:border-accent/50 hover:shadow-lg hover:shadow-accent/5"
            >
              <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-accent/10 text-accent transition-colors group-hover:bg-accent group-hover:text-accent-foreground">
                <Icon className="h-6 w-6" />
              </div>
              <h3 className="mb-3 text-lg font-semibold">{feature.title}</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{feature.description}</p>
            </Card>
          )
        })}
      </div>
    </section>
  )
}
