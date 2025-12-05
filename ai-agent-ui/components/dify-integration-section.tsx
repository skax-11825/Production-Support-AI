import { Card } from "@/components/ui/card"
import { Workflow, Database, MessageSquare } from "lucide-react"
import Image from "next/image"

export function DifyIntegrationSection() {
  return (
    <section id="integration" className="border-y border-border/40 bg-secondary/30 py-32">
      <div className="container mx-auto px-6">
        <div className="mb-12 flex items-center justify-center gap-3">
          <span className="text-4xl font-bold tracking-tight text-foreground">M-axis</span>
          <span className="text-3xl font-light text-muted-foreground">+</span>
          <Image 
            src="/dify.png" 
            alt="Dify" 
            width={80} 
            height={32} 
            className="h-8 w-auto object-contain" 
          />
        </div>

        <div className="mb-16 text-center">
          <h2 className="mb-4 text-4xl font-semibold tracking-tight sm:text-5xl">
            Seamlessly Connected to M-axis & Dify
          </h2>
          <p className="mx-auto max-w-2xl text-balance text-lg leading-relaxed text-muted-foreground">
            Built on SK AX's M-axis manufacturing platform with Dify's powerful AI orchestration, providing a unified
            experience for building and deploying intelligent production agents.
          </p>
        </div>

        <div className="mx-auto grid max-w-4xl gap-6 md:grid-cols-3">
          <Card className="border-border/50 bg-card p-6 transition-all hover:shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500/20 to-teal-500/20 text-emerald-600 dark:text-emerald-400">
              <Workflow className="h-5 w-5" />
            </div>
            <h3 className="mb-2 font-semibold">Workflow Engine</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Leverage Dify's visual workflow builder for custom error handling logic
            </p>
          </Card>

          <Card className="border-border/50 bg-card p-6 transition-all hover:shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-500/20 text-blue-600 dark:text-blue-400">
              <Database className="h-5 w-5" />
            </div>
            <h3 className="mb-2 font-semibold">Knowledge Base</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Connect to Dify's knowledge management for context-aware responses
            </p>
          </Card>

          <Card className="border-border/50 bg-card p-6 transition-all hover:shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20 text-purple-600 dark:text-purple-400">
              <MessageSquare className="h-5 w-5" />
            </div>
            <h3 className="mb-2 font-semibold">LLM Models</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Access multiple AI models through Dify's unified API gateway
            </p>
          </Card>
        </div>
      </div>
    </section>
  )
}
