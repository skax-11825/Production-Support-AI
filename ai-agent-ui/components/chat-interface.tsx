"use client"

import { useState, useEffect, useRef } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Send, User, Loader2, Bot, MessageSquare } from "lucide-react"
import { SettingsDialog } from "@/components/settings-dialog"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

type Message = {
  role: "user" | "assistant"
  content: string
}

type AgentType = "state-chase" | "error-lens"

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
  "error-lens": "app-hKVB2xN9C5deXeavB9SAfkRo",
  "state-chase": "app-XM30CYZpFY9ECH59lH1s1Erg",
}

// 에이전트별 추천 질문 (시연용)
const SUGGESTED_QUESTIONS: Record<AgentType, string[]> = {
  "state-chase": [
    "PAVB814 설비가 현재 멈춰있는데, 대체 가능한 설비 알려줘",
    "OP20, FLASH 제품 투입 가능한 설비 알려줘",
    "OP10, DRAM 우선 투입할 LOT 3개 추천해줘",
    "L990505010 후속 공정 진행 안되는 이유 알려줘",
    "L990505011 진행 안되고 있는 이유 알려줘",
  ],
  "error-lens": [
    "ASML_PH_#018 노광 품질 저하 주요 원인 알려줘",
    "2025년 5월 Cleaning 공정 에러 건수 보여줘",
    "M14-IMP-006 2025년 총 에러 횟수와 주로 조치한 방법 알려줘",
    "정수진 책임이 지금 진행 중인 작업 있어?",
    "M14-ET-008(Lam kiyo) ET_VAC_099 에러 조치 방법 알려줘",
  ],
}

export function ChatInterface({ agentType }: ChatInterfaceProps) {
  const initialMessage =
    agentType === "state-chase"
      ? "안녕하세요! State Trace Agent입니다. 무엇을 도와드릴까요?"
      : "안녕하세요! Error Lens Agent입니다. 무엇을 도와드릴까요?"

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
  const lastUserMessageRef = useRef<HTMLDivElement>(null)
  const chatContainerRef = useRef<HTMLDivElement>(null)

  // 에이전트별 localStorage 키 (v3: State Trace API 키 변경)
  const storageKey = `difyConfig_v3_${agentType}`

  useEffect(() => {
    loadConfig()
  }, [agentType])

  // 페이지 로드 시 채팅창으로 자동 스크롤
  useEffect(() => {
    // 약간의 딜레이 후 스크롤 (페이지 렌더링 완료 후)
    const timer = setTimeout(() => {
      chatContainerRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
    }, 100)
    return () => clearTimeout(timer)
  }, [])

  // 메시지 변경 또는 로딩 시 자동 스크롤 - 사용자 질문이 상단에 오도록
  useEffect(() => {
    // 첫 메시지(환영 메시지)만 있을 때는 스크롤 안 함
    if (messages.length <= 1) return
    
    // 마지막 사용자 메시지가 있으면 해당 위치로 스크롤 (상단 정렬)
    if (lastUserMessageRef.current) {
      lastUserMessageRef.current.scrollIntoView({ behavior: "smooth", block: "start" })
    }
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

  // 추천 질문 클릭 핸들러
  const handleSuggestedQuestion = (question: string) => {
    setInput(question)
  }

  const suggestedQuestions = SUGGESTED_QUESTIONS[agentType]

  return (
    <div ref={chatContainerRef} className="mx-auto max-w-7xl flex gap-6">
      {/* 메인 채팅 영역 */}
      <Card className="flex-1 border-border/50 bg-card">
        <div className="flex h-[600px] flex-col">
          {/* 헤더: 설정 버튼 */}
          <div className="flex items-center justify-between border-b border-border/50 px-4 py-2">
            <h3 className="text-lg font-bold text-foreground">
              {agentType === "state-chase" ? "State Trace Agent" : "Error Lens Agent"}
            </h3>
            <SettingsDialog 
              agentType={agentType} 
              onConfigChange={handleConfigChange} 
            />
          </div>

        {/* 메시지 영역 */}
        <div ref={messagesContainerRef} className="flex-1 space-y-6 overflow-y-auto p-6">
          {messages.map((message, index) => {
            // 마지막 사용자 메시지인지 확인 (이후에 다른 user 메시지가 없는 경우)
            const isLastUserMessage = message.role === "user" && 
              messages.slice(index + 1).every(m => m.role !== "user")
            
            return (
            <div 
              key={index} 
              ref={isLastUserMessage ? lastUserMessageRef : null}
              className={`flex gap-4 ${message.role === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
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
                {message.role === "user" ? (
                <p className="leading-relaxed whitespace-pre-wrap">{message.content}</p>
                ) : (
                  <div className="markdown-content">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {message.content}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
            )
          })}
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
              placeholder={agentType === "state-chase" ? "State Trace에게 질문하세요..." : "Error Lens에게 질문하세요..."}
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

      {/* 추천 질문 사이드바 */}
      <Card className="w-80 shrink-0 border-border/50 bg-card">
        <div className="flex h-[600px] flex-col">
          <div className="border-b border-border/50 px-4 py-3">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5 text-muted-foreground" />
              <h3 className="font-semibold text-foreground">추천 질문</h3>
            </div>
            <p className="mt-1 text-xs text-muted-foreground">클릭하면 입력창에 자동 입력됩니다</p>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            <div className="space-y-3">
              {suggestedQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleSuggestedQuestion(question)}
                  className={`w-full text-left p-3 rounded-xl border transition-all hover:shadow-md ${
                    agentType === "state-chase"
                      ? "border-blue-200 bg-blue-50/50 hover:bg-blue-100/70 hover:border-blue-300 dark:border-blue-800 dark:bg-blue-950/30 dark:hover:bg-blue-900/50"
                      : "border-orange-200 bg-orange-50/50 hover:bg-orange-100/70 hover:border-orange-300 dark:border-orange-800 dark:bg-orange-950/30 dark:hover:bg-orange-900/50"
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <span className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-medium text-white ${
                      agentType === "state-chase"
                        ? "bg-gradient-to-br from-blue-500 to-purple-600"
                        : "bg-gradient-to-br from-orange-500 to-red-600"
                    }`}>
                      {index + 1}
                    </span>
                    <span className="text-sm leading-relaxed text-foreground">{question}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}
