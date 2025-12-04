import { Header } from "@/components/header"
import { ChatInterface } from "@/components/chat-interface"
import { Card } from "@/components/ui/card"
import { AlertCircle, Search, ShieldCheck, Lightbulb } from "lucide-react"

export default function ErrorLensePage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-background to-secondary/20">
      <Header />
      <div className="container mx-auto px-6 pt-32 pb-16">
        <div className="mb-16 text-center">
          <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-orange-500 to-red-600 shadow-xl shadow-red-500/30">
            <AlertCircle className="h-10 w-10 text-white" />
          </div>
          <h1 className="mb-4 text-5xl font-semibold tracking-tight sm:text-6xl">Error Lense</h1>
          <p className="mx-auto max-w-2xl text-balance text-lg leading-relaxed text-muted-foreground">
            Intelligent error detection and resolution system for semiconductor production lines
          </p>
        </div>

        <div className="mb-16 grid gap-6 md:grid-cols-3">
          <Card className="border-border/50 bg-card/50 p-6 backdrop-blur-sm transition-all hover:shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-orange-500/20 to-red-500/20">
              <Search className="h-5 w-5 text-orange-600 dark:text-orange-400" />
            </div>
            <h3 className="mb-2 font-semibold">Error Detection</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Automatically identify and classify production errors in real-time
            </p>
          </Card>

          <Card className="border-border/50 bg-card/50 p-6 backdrop-blur-sm transition-all hover:shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-emerald-500/20 to-teal-500/20">
              <ShieldCheck className="h-5 w-5 text-emerald-600 dark:text-emerald-400" />
            </div>
            <h3 className="mb-2 font-semibold">Root Cause Analysis</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Trace errors back to their source with AI-powered investigation
            </p>
          </Card>

          <Card className="border-border/50 bg-card/50 p-6 backdrop-blur-sm transition-all hover:shadow-lg">
            <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500/20 to-pink-500/20">
              <Lightbulb className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <h3 className="mb-2 font-semibold">Smart Solutions</h3>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Get instant recommendations for error resolution and prevention
            </p>
          </Card>
        </div>

        <ChatInterface agentType="error-lense" />
      </div>
    </main>
  )
}
