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

type DifyAppType = "chatbot" | "workflow" | "completion"
type AuthHeaderType = "bearer" | "api-key" | "x-api-key"

interface DifyConfig {
  difyApiBase: string
  difyApiKey: string
  apiServerUrl: string
  difyAppType: DifyAppType
  authHeaderType: AuthHeaderType
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
          difyAppType: parsed.difyAppType || "chatbot",
          authHeaderType: parsed.authHeaderType || "bearer",
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

    // API Key 검증 및 정리
    // 모든 종류의 공백 문자 제거 (공백, 탭, 줄바꿈 등)
    const rawApiKey = (config.difyApiKey || "").toString()
    const trimmedApiKey = rawApiKey.trim()
    const cleanApiKey = trimmedApiKey.replace(/\s+/g, "") // 모든 공백 제거
    
    if (!trimmedApiKey || !cleanApiKey) {
      throw new Error("API Key가 비어있습니다. 설정에서 API Key를 입력하세요.")
    }

    // URL 정리 및 검증
    let baseUrl = (config.difyApiBase || "").trim()
    
    // 끝의 쉼표, 세미콜론, 공백 제거
    baseUrl = baseUrl.replace(/[,;\s]+$/, "")
    
    // 끝의 슬래시 제거
    baseUrl = baseUrl.replace(/\/+$/, "")
    
    // /v1 경로가 없으면 자동 추가 (일부 Dify 서버는 /v1이 필요함)
    // 단, 포트 번호가 있거나 이미 경로가 있으면 그대로 사용
    if (!baseUrl.match(/\/v\d+$/) && !baseUrl.match(/:\d+\//)) {
      // 포트 번호가 있고 경로가 없는 경우에만 /v1 추가
      if (baseUrl.match(/:\d+$/)) {
        baseUrl = `${baseUrl}/v1`
      } else if (!baseUrl.includes("/", 8)) { // 프로토콜 부분 이후에 슬래시가 없으면
        baseUrl = `${baseUrl}/v1`
      }
    }
    
    // 앱 타입에 따른 엔드포인트 결정
    const appType = config.difyAppType || "workflow"
    let endpoint = "/chat-messages"
    if (appType === "workflow") {
      endpoint = "/workflows/run"
    } else if (appType === "completion") {
      endpoint = "/completion-messages"
    }
    
    const url = `${baseUrl}${endpoint}`
    
    // 앱 타입에 따른 payload 구성
    let payload: Record<string, unknown>
    if (appType === "workflow") {
      // 워크플로우 앱은 다른 payload 형식 사용
      // 워크플로우의 inputs에 query 변수가 정의되어 있어야 함
      payload = {
        inputs: { query: message },
        response_mode: "blocking",
        user: "web-ui-user",
      }
    } else {
      // Chatbot/Completion 앱
      payload = {
        inputs: {},
        query: message,
        response_mode: "blocking",
        conversation_id: conversationId,
        user: "web-ui-user",
      }
    }

    console.log("[Dify API] 요청 시작:", { url, appType, hasKey: !!cleanApiKey, keyLength: cleanApiKey.length })

    try {
      // 프록시를 통해 요청 (CORS 문제 해결)
      const response = await fetch("/api/dify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: url,
          apiKey: cleanApiKey, // 모든 공백 제거된 API Key 전달
          appType: appType, // 앱 타입 전달
          authHeaderType: config.authHeaderType || "bearer", // 인증 헤더 타입
          payload: payload,
        }),
      })

      console.log("[Dify API] 응답 상태:", response.status, response.statusText)

      // 응답 본문을 텍스트로 먼저 읽기
      const responseText = await response.text()
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}: ${response.statusText}`
        try {
          const errorData = JSON.parse(responseText)
          errorMessage = errorData.error || errorData.message || errorMessage
        } catch {
          // JSON 파싱 실패 시 텍스트 그대로 사용
          if (responseText.trim().startsWith("<!DOCTYPE") || responseText.trim().startsWith("<html")) {
            errorMessage = "Dify 서버에서 HTML 페이지를 반환했습니다. URL이 올바른지 확인하세요."
          } else {
            errorMessage = responseText.substring(0, 200) || errorMessage
          }
        }
        console.error("[Dify API] 오류:", errorMessage)
        throw new Error(errorMessage)
      }

      // 성공 응답 파싱
      let data
      try {
        data = JSON.parse(responseText)
      } catch (parseError) {
        console.error("[Dify API] JSON 파싱 실패:", parseError)
        throw new Error("서버에서 유효하지 않은 응답을 받았습니다.")
      }
      
      // 프록시에서 오류가 있으면
      if (data.error) {
        throw new Error(data.error)
      }
      console.log("[Dify API] 응답 성공:", { 
        hasAnswer: !!data.answer, 
        hasOutputs: !!data.outputs, 
        hasConversationId: !!data.conversation_id 
      })
      
      // conversation_id 저장 (chatbot 앱인 경우)
      if (data.conversation_id) {
        setConversationId(data.conversation_id)
      }

      // 워크플로우 응답 처리
      if (appType === "workflow") {
        // 워크플로우 응답은 data.outputs에 결과가 있음
        if (data.outputs) {
          // outputs에서 텍스트 응답 추출 (일반적인 출력 변수명들)
          const output = data.outputs.text || 
                        data.outputs.answer || 
                        data.outputs.result || 
                        data.outputs.output ||
                        data.outputs.response ||
                        JSON.stringify(data.outputs)
          return output
        }
        // data 자체에 answer가 있을 수도 있음
        if (data.answer) {
          return data.answer
        }
        return data.data?.outputs?.text || data.data?.answer || "워크플로우 응답을 처리할 수 없습니다."
      }

      return data.answer || "응답을 받을 수 없습니다."
    } catch (error) {
      console.error("[Dify API] 예외 발생:", error)
      
      // 네트워크 오류 상세 정보
      if (error instanceof TypeError && error.message.includes("fetch")) {
        throw new Error(`네트워크 오류: ${error.message}. 프록시 서버 연결을 확인하세요.`)
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
