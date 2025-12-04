"use client"
import { Bot } from "lucide-react"
import Image from "next/image"

export function Header() {
  return (
    <header className="fixed top-0 left-0 right-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-md">
      <div className="container mx-auto flex h-16 items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-purple-500/20 via-blue-500/20 to-cyan-500/20 border border-purple-500/30">
              <Bot className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
          <span className="text-lg font-semibold">Production Support AI</span>
        </div>

        <nav className="hidden items-center gap-8 md:flex">
          <a href="/" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
            Home
          </a>
          <a href="#agents" className="text-sm text-muted-foreground transition-colors hover:text-foreground">
            AI Agents
          </a>
        </nav>

        <div className="flex items-center gap-4">
          <Image src="/sk-logo.png" alt="SK Group Logo" width={120} height={60} className="h-8 w-auto" priority />
        </div>
      </div>
    </header>
  )
}
