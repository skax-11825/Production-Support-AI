"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Settings, CheckCircle2, XCircle, Eye, EyeOff, Info, ChevronDown, ChevronUp, X } from "lucide-react"

type AgentType = "state-chase" | "error-lense"

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

interface SettingsDialogProps {
  agentType: AgentType
  onConfigChange?: (config: DifyConfig) => void
}

export function SettingsDialog({ agentType, onConfigChange }: SettingsDialogProps) {
  // 에이전트별 localStorage 키 (v3: State Trace API 키 변경)
  const storageKey = `difyConfig_v3_${agentType}`
  const defaultApiKey = DEFAULT_API_KEYS[agentType]
  
  const [open, setOpen] = useState(false)
  const [config, setConfig] = useState<DifyConfig>({
    difyApiBase: DEFAULT_BASE_URL,
    difyApiKey: defaultApiKey,
    apiServerUrl: DEFAULT_NGROK_URL,
  })
  const [apiServerStatus, setApiServerStatus] = useState<{ connected: boolean; message: string } | null>(null)
  const [difyStatus, setDifyStatus] = useState<{ connected: boolean; message: string } | null>(null)
  const [showApiKey, setShowApiKey] = useState(false)
  const [showErrorDetails, setShowErrorDetails] = useState(false)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = () => {
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
        console.error("Failed to load settings:", e)
      }
    } else {
      // 저장된 설정이 없으면 기본값 저장
      const newConfig = {
        difyApiBase: DEFAULT_BASE_URL,
        difyApiKey: defaultApiKey,
        apiServerUrl: DEFAULT_NGROK_URL,
      }
      setConfig(newConfig)
      localStorage.setItem(storageKey, JSON.stringify(newConfig))
    }
  }

  const saveSettings = () => {
    localStorage.setItem(storageKey, JSON.stringify(config))
    onConfigChange?.(config)
    setOpen(false)
  }

  const checkApiServerStatus = async () => {
    if (!config.apiServerUrl) {
      setApiServerStatus({ connected: false, message: "URL을 입력하세요" })
      return
    }

    try {
      const cleanedUrl = config.apiServerUrl.trim().replace(/[,;\/]+$/, "")
      const response = await fetch(`/api/health?url=${encodeURIComponent(cleanedUrl)}`)
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }
      
      const data = await response.json()
      
      if (data.error) {
        throw new Error(data.error)
      }

      setApiServerStatus({
        connected: data.status === "healthy",
        message: data.status === "healthy" ? "정상" : "비정상",
      })
    } catch (error) {
      setApiServerStatus({
        connected: false,
        message: `연결 실패: ${error instanceof Error ? error.message : "알 수 없는 오류"}`,
      })
    }
  }

  const checkDifyStatus = async () => {
    if (!config.difyApiKey) {
      setDifyStatus({ connected: false, message: "API Key를 입력하세요" })
      return
    }

    if (!config.difyApiBase) {
      setDifyStatus({ connected: false, message: "Dify API Base URL을 입력하세요" })
      return
    }

    if (!config.apiServerUrl) {
      setDifyStatus({ connected: false, message: "API 서버 URL(Ngrok)을 입력하세요" })
      return
    }

    try {
      const cleanApiKey = config.difyApiKey.trim().replace(/\s+/g, "")
      
      if (!cleanApiKey || cleanApiKey.length < 10) {
        setDifyStatus({ connected: false, message: "API Key가 올바르지 않습니다" })
        return
      }
      
      // URL 정리
      let baseUrl = config.difyApiBase.trim().replace(/[,;\s\/]+$/, "")
      
      // /v1이 없으면 추가
      if (!baseUrl.match(/\/v\d+$/)) {
        baseUrl = `${baseUrl}/v1`
      }
      
      const url = `${baseUrl}/chat-messages`
      
      // Ngrok 프록시 사용
      const ngrokUrl = config.apiServerUrl.trim().replace(/\/+$/, "")
      const proxyUrl = `${ngrokUrl}/proxy/dify`
      
      console.log("[Dify] 연결 테스트:", { url, proxyUrl })
      
      const response = await fetch(proxyUrl, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: url,
          apiKey: cleanApiKey,
          appType: "chatbot",
          authHeaderType: "bearer",
          payload: {
            inputs: {},
            query: "테스트",
            response_mode: "blocking",
            user: "web-ui-user",
          },
        }),
      })

      const responseText = await response.text()
      
      if (!response.ok) {
        let errorMessage = `HTTP ${response.status}`
        try {
          const errorData = JSON.parse(responseText)
          errorMessage = errorData.error || errorData.message || errorMessage
        } catch {
          errorMessage = responseText.substring(0, 300) || errorMessage
        }
        throw new Error(errorMessage)
      }

      const data = JSON.parse(responseText)
      
      if (data.error) {
        throw new Error(data.error)
      }

      setDifyStatus({ connected: true, message: "연결 성공" })
    } catch (error) {
      setDifyStatus({
        connected: false,
        message: error instanceof Error ? error.message : "연결 실패",
      })
    }
  }

  const checkAllStatus = async () => {
    setApiServerStatus(null)
    setDifyStatus(null)
    await Promise.all([checkApiServerStatus(), checkDifyStatus()])
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="outline" size="icon">
          <Settings className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>설정</DialogTitle>
          <DialogDescription>Dify API 및 서버 연결 설정을 관리합니다.</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Dify API Base URL */}
          <div className="space-y-2">
            <Label htmlFor="difyApiBase">Dify API Base URL</Label>
            <Input
              id="difyApiBase"
              placeholder="https://ai-platform-deploy.koreacentral.cloudapp.azure.com:3000/v1"
              value={config.difyApiBase}
              onChange={(e) => setConfig({ ...config, difyApiBase: e.target.value })}
            />
            <p className="text-xs text-muted-foreground">
              포트 번호를 포함한 전체 URL (예: https://server.com:3000/v1)
            </p>
          </div>

          {/* Dify API Key */}
          <div className="space-y-2">
            <Label htmlFor="difyApiKey">Dify API Key</Label>
            <div className="relative">
              <Input
                id="difyApiKey"
                type={showApiKey ? "text" : "password"}
                placeholder="app-xxxxxxxx"
                value={config.difyApiKey}
                onChange={(e) => setConfig({ ...config, difyApiKey: e.target.value })}
                className="pr-10"
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                onClick={() => setShowApiKey(!showApiKey)}
              >
                {showApiKey ? (
                  <EyeOff className="h-4 w-4 text-muted-foreground" />
                ) : (
                  <Eye className="h-4 w-4 text-muted-foreground" />
                )}
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">Dify 대시보드에서 발급받은 API Key</p>
          </div>

          {/* API 서버 URL (Ngrok) */}
          <div className="space-y-2">
            <Label htmlFor="apiServerUrl">API 서버 URL (Ngrok)</Label>
            <Input
              id="apiServerUrl"
              placeholder="https://your-ngrok-url.ngrok-free.dev"
              value={config.apiServerUrl}
              onChange={(e) => setConfig({ ...config, apiServerUrl: e.target.value })}
            />
            <p className="text-xs text-muted-foreground">로컬 FastAPI 서버의 Ngrok URL</p>
          </div>

          {/* 안내 메시지 */}
          <div className="flex items-start gap-2 rounded-md bg-blue-50 dark:bg-blue-950 p-3 text-xs">
            <Info className="h-4 w-4 mt-0.5 text-blue-500 shrink-0" />
            <div className="text-blue-700 dark:text-blue-300 space-y-1">
              <p className="font-medium">연결 흐름:</p>
              <p>UI → Ngrok → 로컬 서버 → Dify 서버</p>
              <p className="text-blue-600 dark:text-blue-400">
                * 로컬 서버가 실행 중이어야 합니다
              </p>
            </div>
          </div>

          {/* 시스템 상태 */}
          <div className="space-y-2 rounded-lg border p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">시스템 상태</span>
              <Button variant="outline" size="sm" onClick={checkAllStatus}>
                확인
              </Button>
            </div>
            <div className="space-y-2 pt-2">
              {/* API 서버 상태 */}
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">API 서버 (Ngrok):</span>
                {apiServerStatus ? (
                  <div className="flex items-center gap-2">
                    {apiServerStatus.connected ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className={apiServerStatus.connected ? "text-green-500" : "text-red-500"}>
                      {apiServerStatus.message}
                    </span>
                  </div>
                ) : (
                  <span className="text-muted-foreground">-</span>
                )}
              </div>

              {/* Dify 상태 */}
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Dify 연결:</span>
                {difyStatus ? (
                  <div className="flex items-center gap-2">
                    {difyStatus.connected ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className={difyStatus.connected ? "text-green-500" : "text-red-500"}>
                      {difyStatus.connected ? "정상" : "연결 실패"}
                    </span>
                    {!difyStatus.connected && difyStatus.message && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-6 px-2 text-xs"
                        onClick={() => setShowErrorDetails(!showErrorDetails)}
                      >
                        {showErrorDetails ? (
                          <>숨기기 <ChevronUp className="h-3 w-3 ml-1" /></>
                        ) : (
                          <>상세 <ChevronDown className="h-3 w-3 ml-1" /></>
                        )}
                      </Button>
                    )}
                  </div>
                ) : (
                  <span className="text-muted-foreground">-</span>
                )}
              </div>

              {/* 에러 상세 (스크롤 가능) */}
              {difyStatus && !difyStatus.connected && showErrorDetails && (
                <div className="relative mt-2 p-2 rounded bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="absolute top-1 right-1 h-5 w-5 z-10"
                    onClick={() => {
                      setShowErrorDetails(false)
                      setDifyStatus(null)
                    }}
                  >
                    <X className="h-3 w-3" />
                  </Button>
                  <div className="max-h-40 overflow-y-auto pr-6">
                    <p className="text-xs text-red-700 dark:text-red-300 whitespace-pre-line">
                      {difyStatus.message}
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)}>
            취소
          </Button>
          <Button onClick={saveSettings}>저장</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
