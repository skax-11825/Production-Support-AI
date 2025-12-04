import { HeroSection } from "@/components/hero-section"
import { SystemWorkflow } from "@/components/semiconductor-features"
import { AgentNavigation } from "@/components/agent-navigation"
import { DifyIntegrationSection } from "@/components/dify-integration-section"
import { WorkflowSection } from "@/components/workflow-section"
import { Header } from "@/components/header"

export default function Home() {
  return (
    <main className="min-h-screen">
      <Header />
      <HeroSection />
      <SystemWorkflow />
      <AgentNavigation />
      <DifyIntegrationSection />
      <WorkflowSection />
    </main>
  )
}
