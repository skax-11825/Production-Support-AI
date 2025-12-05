"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, Bot, User, Loader2 } from "lucide-react"
import { SettingsDialog } from "@/components/settings-dialog"

type Message = {
  role: "user" | "assistant"
  content: string
}

type AgentType = "lot-scheduling" | "error-lense"

interface ChatInterfaceProps {
  agentType: AgentType
}

interface DifyConfig {
  difyApiBase: string
  difyApiKey: string
  apiServerUrl: string
}

export function ChatInterface({ agentType }: ChatInterfaceProps) {
  const initialMessage =
    agentType === "lot-scheduling"
      ? "Hello! I'm the LOT Scheduling Agent. I can help you optimize production schedules, allocate resources efficiently, and manage lot priorities. What would you like to schedule today?"
      : "Hello! I'm Error Lense AI. I can help you analyze errors, identify root causes, and suggest solutions for your manufacturing systems. What issue can I help you investigate?"

  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content: initialMessage,
    },
  ])
  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [config, setConfig] = useState<DifyConfig | null>(null)
  const [conversationId, setConversationId] = useState<string | null>(null)

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = () => {
    const saved = localStorage.getItem("difyConfig")
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        setConfig({
          difyApiBase: parsed.difyApiBase || "",
          difyApiKey: parsed.difyApiKey || "",
          apiServerUrl: parsed.apiServerUrl || "http://localhost:8000",
        })
      } catch (e) {
        console.error("Failed to load config:", e)
      }
    }
  }

  const handleConfigChange = (newConfig: DifyConfig) => {
    setConfig(newConfig)
  }

  const sendMessageToDify = async (message: string): Promise<string> => {
    if (!config || !config.difyApiKey || !config.difyApiBase) {
      throw new Error("Dify API 설정이 완료되지 않았습니다. 설정 버튼을 클릭하여 API Key를 입력하세요.")
    }

    // URL 정리 (공백, 쉼표 제거, 끝의 슬래시 제거)
    const cleanedBase = config.difyApiBase.trim().replace(/[,;]$/, "").replace(/\/$/, "")
    const url = `${cleanedBase}/chat-messages`
    const payload = {
      inputs: {},
      query: message,
      response_mode: "blocking" as const,
      conversation_id: conversationId,
      user: "web-ui-user",
    }

    console.log("[Dify API] 요청 시작:", { url, hasKey: !!config.difyApiKey })

    try {
      // 프록시를 통해 요청 (CORS 문제 해결)
      const response = await fetch("/api/dify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: url,
          apiKey: config.difyApiKey,
          payload: payload,
        }),
      })

      console.log("[Dify API] 응답 상태:", response.status, response.statusText)

      if (!response.ok) {
        const errorText = await response.text()
        console.error("[Dify API] 오류 응답 텍스트:", errorText.substring(0, 200))
        
        // HTML 응답인지 확인
        if (errorText.trim().startsWith("<!DOCTYPE") || errorText.trim().startsWith("<html")) {
          throw new Error("Dify 서버에서 HTML 페이지를 반환했습니다. URL이 올바른지 확인하세요.")
        }
        
        try {
          const errorData = JSON.parse(errorText)
          const errorMessage = errorData.message || errorData.error || `HTTP ${response.status}: ${response.statusText}`
          console.error("[Dify API] 오류:", errorMessage, errorData)
          throw new Error(errorMessage)
        } catch (parseError) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
      }

      const data = await response.json()
      
      // 프록시에서 오류가 있으면
      if (data.error) {
        throw new Error(data.error)
      }
      console.log("[Dify API] 응답 성공:", { hasAnswer: !!data.answer, hasConversationId: !!data.conversation_id })
      
      // conversation_id 저장
      if (data.conversation_id) {
        setConversationId(data.conversation_id)
      }

      return data.answer || "응답을 받을 수 없습니다."
    } catch (error) {
      console.error("[Dify API] 예외 발생:", error)
      
      // 네트워크 오류 상세 정보
      if (error instanceof TypeError && error.message.includes("fetch")) {
        if (url.startsWith("http://") && window.location.protocol === "https:") {
          throw new Error("Mixed Content 오류: HTTPS 페이지에서 HTTP 리소스에 접근할 수 없습니다. Dify API URL을 HTTPS로 변경하세요.")
        }
        throw new Error(`네트워크 오류: ${error.message}. CORS 또는 네트워크 연결을 확인하세요.`)
      }
      
      throw error
    }
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = { role: "user", content: input }
    setMessages((prev) => [...prev, userMessage])
    const currentInput = input
    setInput("")
    setIsLoading(true)

    try {
      // Dify API 호출
      const response = await sendMessageToDify(currentInput)
      const aiMessage: Message = {
        role: "assistant",
        content: response,
      }
      setMessages((prev) => [...prev, aiMessage])
    } catch (error) {
      const errorMessage: Message = {
        role: "assistant",
        content: `오류: ${error instanceof Error ? error.message : "알 수 없는 오류가 발생했습니다."}`,
      }
      setMessages((prev) => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card className="mx-auto max-w-5xl border-border/50 bg-card">
      <div className="flex h-[600px] flex-col">
        {/* 헤더: 설정 버튼 */}
        <div className="flex items-center justify-between border-b border-border/50 p-4">
          <h3 className="text-sm font-medium text-muted-foreground">
            {agentType === "lot-scheduling" ? "LOT Scheduling Agent" : "Error Lense AI"}
          </h3>
          <SettingsDialog onConfigChange={handleConfigChange} />
        </div>

        {/* 메시지 영역 */}
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
                <p className="leading-relaxed whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-4">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent text-accent-foreground">
                <Bot className="h-5 w-5" />
              </div>
              <div className="max-w-[70%] rounded-2xl bg-muted px-4 py-3">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-muted-foreground">처리 중...</span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* 입력 영역 */}
        <div className="border-t border-border/50 p-6">
          <div className="flex gap-3">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && !isLoading && handleSend()}
              placeholder={`Ask ${agentType === "lot-scheduling" ? "LOT Scheduling Agent" : "Error Lense"} anything...`}
              className="flex-1 rounded-full border-border/50 bg-secondary/50 px-6"
              disabled={isLoading}
            />
            <Button 
              onClick={handleSend} 
              size="icon" 
              className="h-11 w-11 shrink-0 rounded-full"
              disabled={isLoading || !input.trim()}
            >
              {isLoading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
              <Send className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </Card>
  )
}
