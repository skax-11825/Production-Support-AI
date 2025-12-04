"use client"

import { Button } from "@/components/ui/button"
import { Bot } from "lucide-react"

export function HeroSection() {
  const scrollToAgents = () => {
    document.getElementById("agents")?.scrollIntoView({ behavior: "smooth" })
  }

  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden px-6 pt-16">
      {/* Subtle grid background */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]" />

      <div className="relative z-10 mx-auto max-w-5xl text-center">
        <div className="mx-auto mb-8 flex items-center justify-center gap-2 animate-fade-in-up">
          <div className="flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-purple-500/20 via-blue-500/20 to-cyan-500/20 shadow-xl shadow-purple-500/20 backdrop-blur-sm border border-purple-500/30">
            <Bot className="h-10 w-10 text-purple-600 dark:text-purple-400" />
          </div>
        </div>

        <h1 className="mb-4 text-5xl font-semibold tracking-tight text-foreground sm:text-7xl animate-fade-in-up animation-delay-100">
          Welcome to the
        </h1>
        <h1 className="mb-2 bg-gradient-to-r from-blue-600 via-purple-600 to-green-600 bg-clip-text text-5xl font-bold tracking-tight text-transparent sm:text-7xl animate-fade-in-up animation-delay-200">
          Production Support AI
        </h1>
        <p className="mb-6 text-xl font-medium text-muted-foreground/80 sm:text-2xl animate-fade-in-up animation-delay-250">
          Agentic AI Dev Part
        </p>

        <p className="mx-auto mb-12 max-w-2xl text-balance text-lg leading-relaxed text-muted-foreground sm:text-xl animate-fade-in-up animation-delay-300">
          Intelligent production management and error resolution powered by advanced AI agents. Built for SK Group with
          seamless Maxis and Dify integration.
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col items-center justify-center gap-4 sm:flex-row animate-fade-in-up animation-delay-400">
          <Button size="lg" className="rounded-full px-8 text-base" onClick={scrollToAgents}>
            Direct to Agents
          </Button>
          <Button size="lg" variant="outline" className="rounded-full px-8 text-base bg-transparent">
            Watch Demo
          </Button>
        </div>

        {/* Scroll Indicator */}
        <div className="absolute bottom-12 left-1/2 -translate-x-1/2 animate-bounce">
          <div className="h-8 w-5 rounded-full border-2 border-muted-foreground/30">
            <div className="mx-auto mt-2 h-2 w-1 rounded-full bg-muted-foreground/50" />
          </div>
        </div>
      </div>
    </section>
  )
}
