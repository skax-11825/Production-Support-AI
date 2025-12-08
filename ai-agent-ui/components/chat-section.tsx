"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, Bot, User } from "lucide-react"

type Message = {
  role: "user" | "assistant"
  content: string
}

export function ChatSection() {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I'm Error Lens AI. I can help you analyze errors, suggest solutions, and answer questions about your systems. How can I assist you today?",
    },
  ])
  const [input, setInput] = useState("")

  const handleSend = () => {
    if (!input.trim()) return

    const userMessage: Message = { role: "user", content: input }
    setMessages((prev) => [...prev, userMessage])
    setInput("")

    // Simulate AI response
    setTimeout(() => {
      const aiMessage: Message = {
        role: "assistant",
        content:
          "I've analyzed your request. Based on the error patterns in your system, I recommend checking the database connection pool settings. This is a demo response - in production, Error Lens would provide detailed analysis powered by Dify workflows.",
      }
      setMessages((prev) => [...prev, aiMessage])
    }, 1000)
  }

  return (
    <section id="chat" className="border-t border-border/40 bg-secondary/30 py-32">
      <div className="container mx-auto px-6">
        <div className="mb-16 text-center">
          <h2 className="mb-4 text-4xl font-semibold tracking-tight sm:text-5xl">Try Error Lens Now</h2>
          <p className="mx-auto max-w-2xl text-balance text-lg leading-relaxed text-muted-foreground">
            Experience the power of agentic AI. Ask questions, analyze errors, or explore how Error Lens can help your
            team.
          </p>
        </div>

        <Card className="mx-auto max-w-4xl border-border/50 bg-card">
          {/* Chat Messages */}
          <div className="flex h-[500px] flex-col">
            <div className="flex-1 space-y-6 overflow-y-auto p-6">
              {messages.map((message, index) => (
                <div key={index} className={`flex gap-4 ${message.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                  <div
                    className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
                      message.role === "user" ? "bg-secondary" : "bg-accent text-accent-foreground"
                    }`}
                  >
                    {message.role === "user" ? <User className="h-5 w-5" /> : <Bot className="h-5 w-5" />}
                  </div>
                  <div
                    className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                      message.role === "user" ? "bg-secondary text-foreground" : "bg-muted text-foreground"
                    }`}
                  >
                    <p className="leading-relaxed">{message.content}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Input Area */}
            <div className="border-t border-border/50 p-6">
              <div className="flex gap-3">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && handleSend()}
                  placeholder="Ask Error Lens anything..."
                  className="flex-1 rounded-full border-border/50 bg-secondary/50 px-6"
                />
                <Button onClick={handleSend} size="icon" className="h-11 w-11 shrink-0 rounded-full">
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </section>
  )
}
