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
            M-axis 플랫폼과 Dify의 자유로운 연동
          </h2>
          <p className="mx-auto max-w-2xl text-balance text-lg leading-relaxed text-muted-foreground">
            제조 표준 AI 플랫폼 'M-axis'와 Dify의 통합으로 다양한 제조 솔루션을 제공합니다.
          </p>
        </div>

        {/* Workflow 동영상 */}
        <div className="mx-auto mb-8 max-w-4xl">
          <div className="overflow-hidden rounded-2xl border border-border/50 shadow-lg">
            <video 
              className="w-full" 
              autoPlay 
              loop 
              muted 
              playsInline
            >
              <source src="/dify_workflow.mp4" type="video/mp4" />
              Your browser does not support the video tag.
            </video>
          </div>
        </div>

        <div className="mx-auto grid max-w-4xl gap-6 md:grid-cols-3">
          <Card className="border-border/50 bg-card p-6">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500/20 to-teal-500/20 text-emerald-600 dark:text-emerald-400">
              <Workflow className="h-5 w-5" />
            </div>
            <h3 className="mb-2 font-semibold">Dify Workflow</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Dify의 워크플로우 빌더를 사용하여 다양한 제조 솔루션을 구축합니다.
            </p>
          </Card>

          <Card className="border-border/50 bg-card p-6">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500/20 to-cyan-500/20 text-blue-600 dark:text-blue-400">
              <Database className="h-5 w-5" />
            </div>
            <h3 className="mb-2 font-semibold">지식 기반 서비스</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              자연어 질의응답을 위한 지식 기반 서비스를 제공합니다.
            </p>
          </Card>

          <Card className="border-border/50 bg-card p-6">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20 text-purple-600 dark:text-purple-400">
              <MessageSquare className="h-5 w-5" />
            </div>
            <h3 className="mb-2 font-semibold">LLM 기반의 에이전트</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              API 호출을 통해 다양한 LLM 기반의 에이전트를 사용할 수 있습니다.
            </p>
          </Card>
        </div>
      </div>
    </section>
  )
}
