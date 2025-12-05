"use client"

import { useState, useEffect, useRef } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, User, Loader2, Bot } from "lucide-react"
import { SettingsDialog } from "@/components/settings-dialog"

type Message = {
  role: "user" | "assistant"
  content: string
}

type AgentType = "state-chase" | "error-lense"

interface ChatInterfaceProps {
  agentType: AgentType
}

interface DifyConfig {
  difyApiBase: string
  difyApiKey: string
  apiServerUrl: string
}

// 공통 기본 설정
const DEFAULT_BASE_URL = "https://ai-platform-deploy.koreacentral.cloudapp.azure.com:3000/v1"
const DEFAULT_NGROK_URL = "https://youlanda-unconciliatory-unmirthfully.ngrok-free.dev"

// 에이전트별 기본 API Key
const DEFAULT_API_KEYS: Record<AgentType, string> = {
  "error-lense": "app-hKVB2xN9C5deXeavB9SAfkRo",
  "state-chase": "app-XM30CYZpFY9ECH59lH1s1Erg",
}

export function ChatInterface({ agentType }: ChatInterfaceProps) {
  const initialMessage =
    agentType === "state-chase"
      ? "안녕하세요! State Chase Agent입니다. 무엇을 도와드릴까요?"
      : "안녕하세요! Error Lense Agent입니다. 무엇을 도와드릴까요?"

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
  
  // 자동 스크롤을 위한 ref
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  // 에이전트별 localStorage 키 (v3: State Chase API 키 변경)
  const storageKey = `difyConfig_v3_${agentType}`

  useEffect(() => {
    loadConfig()
  }, [agentType])

  // 메시지 변경 또는 로딩 시 자동 스크롤
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, isLoading])

  const loadConfig = () => {
    const defaultApiKey = DEFAULT_API_KEYS[agentType]
    const saved = localStorage.getItem(storageKey)
    
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        // 저장된 값이 빈 문자열이면 기본값 사용
        setConfig({
          difyApiBase: parsed.difyApiBase || DEFAULT_BASE_URL,
          difyApiKey: parsed.difyApiKey || defaultApiKey,
          apiServerUrl: parsed.apiServerUrl || DEFAULT_NGROK_URL,
        })
      } catch (e) {
        console.error("Failed to load config:", e)
        // 파싱 실패 시 기본값 사용
        setConfig({
          difyApiBase: DEFAULT_BASE_URL,
          difyApiKey: defaultApiKey,
          apiServerUrl: DEFAULT_NGROK_URL,
        })
      }
    } else {
      // 저장된 설정이 없으면 기본값으로 초기화하고 저장
      const newConfig = {
        difyApiBase: DEFAULT_BASE_URL,
        difyApiKey: defaultApiKey,
        apiServerUrl: DEFAULT_NGROK_URL,
      }
      setConfig(newConfig)
      localStorage.setItem(storageKey, JSON.stringify(newConfig))
    }
  }

  const handleConfigChange = (newConfig: DifyConfig) => {
    setConfig(newConfig)
    localStorage.setItem(storageKey, JSON.stringify(newConfig))
  }

  const sendMessageToDify = async (message: string): Promise<string> => {
    if (!config || !config.difyApiKey || !config.difyApiBase) {
      throw new Error("Dify API 설정이 완료되지 않았습니다. 설정 버튼을 클릭하여 설정을 완료하세요.")
    }

    if (!config.apiServerUrl) {
      throw new Error("API 서버 URL(Ngrok)이 설정되지 않았습니다. 설정에서 Ngrok URL을 입력하세요.")
    }

    // API Key 정리
    const cleanApiKey = config.difyApiKey.trim().replace(/\s+/g, "")
    
    if (!cleanApiKey) {
      throw new Error("API Key가 비어있습니다.")
    }

    // URL 정리 - 끝의 슬래시, 쉼표 등 제거
    let baseUrl = config.difyApiBase.trim().replace(/[,;\s\/]+$/, "")
    
    // /v1이 없으면 추가
    if (!baseUrl.match(/\/v\d+$/)) {
      baseUrl = `${baseUrl}/v1`
    }
    
    // 챗봇 엔드포인트 (고정)
    const url = `${baseUrl}/chat-messages`
    
    // 챗봇 페이로드 (고정)
    const payload = {
      inputs: {},
      query: message,
      response_mode: "blocking",
      conversation_id: conversationId || "",
      user: "web-ui-user",
    }

    // Ngrok 프록시 URL (고정)
    const ngrokUrl = config.apiServerUrl.trim().replace(/\/+$/, "")
    const proxyUrl = `${ngrokUrl}/proxy/dify`

    console.log("[Dify API] 요청:", { url, proxyUrl })

    try {
      const response = await fetch(proxyUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: url,
          apiKey: cleanApiKey,
          appType: "chatbot",  // 고정
          authHeaderType: "bearer",  // 고정
          payload: payload,
        }),
      })

      const responseText = await response.text()
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`
        try {
          const errorData = JSON.parse(responseText)
          errorMessage = errorData.error || errorData.message || errorMessage
        } catch {
          errorMessage = responseText.substring(0, 200) || errorMessage
        }
        throw new Error(errorMessage)
      }

      const data = JSON.parse(responseText)
      
      if (data.error) {
        throw new Error(data.error)
      }

      // conversation_id 저장
      if (data.conversation_id) {
        setConversationId(data.conversation_id)
      }

      return data.answer || "응답을 받을 수 없습니다."
    } catch (error) {
      console.error("[Dify API] 오류:", error)
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
            {agentType === "state-chase" ? "State Chase Agent" : "Error Lense Agent"}
          </h3>
          <SettingsDialog 
            agentType={agentType} 
            onConfigChange={handleConfigChange} 
          />
        </div>

        {/* 메시지 영역 */}
        <div ref={messagesContainerRef} className="flex-1 space-y-6 overflow-y-auto p-6">
          {messages.map((message, index) => (
            <div key={index} className={`flex gap-4 ${message.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
              <div
                className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
                  message.role === "user" 
                    ? "bg-secondary" 
                    : agentType === "state-chase"
                      ? "bg-gradient-to-br from-blue-500 to-purple-600"
                      : "bg-gradient-to-br from-orange-500 to-red-600"
                }`}
              >
                {message.role === "user" ? (
                  <User className="h-5 w-5" />
                ) : (
                  <Bot className="h-5 w-5 text-white" />
                )}
              </div>
              <div
                className={`max-w-[70%] rounded-2xl px-4 py-3 ${
                  message.role === "user" 
                    ? "bg-secondary text-foreground" 
                    : "bg-white dark:bg-slate-800 text-foreground border border-border/50 shadow-sm"
                }`}
              >
                <p className="leading-relaxed whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex gap-4">
              <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
                agentType === "state-chase"
                  ? "bg-gradient-to-br from-blue-500 to-purple-600"
                  : "bg-gradient-to-br from-orange-500 to-red-600"
              }`}>
                <Bot className="h-5 w-5 text-white" />
              </div>
              <div className="max-w-[70%] rounded-2xl bg-white dark:bg-slate-800 border border-border/50 shadow-sm px-4 py-3">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span className="text-muted-foreground">처리 중...</span>
                </div>
              </div>
            </div>
          )}
          {/* 자동 스크롤 타겟 */}
          <div ref={messagesEndRef} />
        </div>

        {/* 입력 영역 */}
        <div className="border-t border-border/50 p-6">
          <div className="flex gap-3">
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && !isLoading && handleSend()}
              placeholder={agentType === "state-chase" ? "State Chase에게 질문하세요..." : "Error Lense에게 질문하세요..."}
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
