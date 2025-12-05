"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Settings, CheckCircle2, XCircle } from "lucide-react"

interface DifyConfig {
  difyApiBase: string
  difyApiKey: string
  apiServerUrl: string
}

interface SettingsDialogProps {
  onConfigChange?: (config: DifyConfig) => void
}

export function SettingsDialog({ onConfigChange }: SettingsDialogProps) {
  const [open, setOpen] = useState(false)
  const [config, setConfig] = useState<DifyConfig>({
    difyApiBase: "",
    difyApiKey: "",
    apiServerUrl: "",
  })
  const [apiServerStatus, setApiServerStatus] = useState<{ connected: boolean; message: string } | null>(null)
  const [difyStatus, setDifyStatus] = useState<{ connected: boolean; message: string } | null>(null)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = () => {
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
        console.error("Failed to load settings:", e)
      }
    }
  }

  const saveSettings = () => {
    localStorage.setItem("difyConfig", JSON.stringify(config))
    onConfigChange?.(config)
    setOpen(false)
  }

  const checkApiServerStatus = async () => {
    try {
      // URL 정리 (공백, 쉼표 제거)
      const cleanedUrl = config.apiServerUrl.trim().replace(/[,;]$/, "")
      console.log("[API Server] 상태 확인:", cleanedUrl)
      
      // 프록시를 통해 요청 (CORS 및 Mixed Content 문제 해결)
      // 프록시는 서버 사이드에서 실행되므로 HTTP/HTTPS 모두 가능
      const response = await fetch(`/api/health?url=${encodeURIComponent(cleanedUrl)}`)
      console.log("[API Server] 응답 상태:", response.status)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: "Unknown error" }))
        throw new Error(errorData.error || `HTTP ${response.status}`)
      }
      
      const data = await response.json()
      
      // 프록시에서 오류가 있으면
      if (data.error) {
        throw new Error(data.error)
      }
      setApiServerStatus({
        connected: data.status === "healthy",
        message: data.status === "healthy" ? "정상" : "비정상",
      })
    } catch (error) {
      console.error("[API Server] 오류:", error)
      
      let errorMessage = error instanceof Error ? error.message : "알 수 없는 오류"
      
      // 네트워크 오류 상세화
      if (error instanceof TypeError) {
        if (error.message.includes("Failed to fetch")) {
          errorMessage = "네트워크 오류: CORS 또는 연결 문제. Ngrok URL이 올바른지 확인하세요."
        }
      }
      
      setApiServerStatus({
        connected: false,
        message: `연결 실패: ${errorMessage}`,
      })
    }
  }

  const checkDifyStatus = async () => {
    if (!config.difyApiKey) {
      setDifyStatus({ connected: false, message: "API Key가 설정되지 않았습니다." })
      return
    }

    if (!config.difyApiBase) {
      setDifyStatus({ connected: false, message: "Dify API Base URL이 설정되지 않았습니다." })
      return
    }

    try {
      // API Key 검증
      if (!config.difyApiKey || !config.difyApiKey.trim()) {
        setDifyStatus({
          connected: false,
          message: "API Key를 입력하세요.",
        })
        return
      }

      // 사용자가 입력한 URL을 그대로 사용
      const url = `${config.difyApiBase}/chat-messages`
      console.log("[Dify] 연결 테스트:", url)
      console.log("[Dify] API Key 길이:", config.difyApiKey.trim().length)
      
      // 프록시를 통해 요청 (CORS 및 Mixed Content 문제 해결)
      // 프록시는 서버 사이드에서 실행되므로 HTTP/HTTPS 모두 가능
      const response = await fetch("/api/dify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: url,
          apiKey: config.difyApiKey.trim(), // API Key 앞뒤 공백 제거
          payload: {
            inputs: {},
            query: "테스트",
            response_mode: "blocking",
            user: "web-ui-user",
          },
        }),
      })

      console.log("[Dify] 응답 상태:", response.status)

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
        throw new Error(errorMessage)
      }

      // 성공 응답 파싱
      let data
      try {
        data = JSON.parse(responseText)
      } catch (parseError) {
        throw new Error("서버에서 유효하지 않은 응답을 받았습니다.")
      }
      
      // 프록시에서 오류가 있으면
      if (data.error) {
        throw new Error(data.error)
      }

      setDifyStatus({ connected: true, message: "연결 성공" })
    } catch (error) {
      console.error("[Dify] 예외:", error)
      
      let errorMessage = error instanceof Error ? error.message : "연결 실패"
      
      // 네트워크 오류 상세화
      if (error instanceof TypeError) {
        if (error.message.includes("Failed to fetch")) {
          errorMessage = "네트워크 오류: CORS 문제 또는 연결 실패. Dify 서버의 CORS 설정을 확인하세요. (자체 호스팅 Dify인 경우 CORS 허용 필요)"
        }
      }
      
      setDifyStatus({
        connected: false,
        message: errorMessage,
      })
    }
  }

  const checkAllStatus = async () => {
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
          <div className="space-y-2">
            <Label htmlFor="difyApiBase">Dify API Base URL</Label>
            <Input
              id="difyApiBase"
              placeholder="https://api.dify.ai/v1"
              value={config.difyApiBase}
              onChange={(e) => setConfig({ ...config, difyApiBase: e.target.value })}
            />
            <p className="text-xs text-muted-foreground">자체 호스팅 시 전체 URL을 입력하세요 (예: https://your-server.com/v1)</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="difyApiKey">Dify API Key</Label>
            <Input
              id="difyApiKey"
              type="password"
              placeholder="app-xxxxxxxx"
              value={config.difyApiKey}
              onChange={(e) => setConfig({ ...config, difyApiKey: e.target.value })}
            />
            <p className="text-xs text-muted-foreground">Dify Chat 애플리케이션에서 발급받은 API Key를 입력하세요</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="apiServerUrl">API 서버 URL</Label>
            <Input
              id="apiServerUrl"
              placeholder="http://localhost:8000"
              value={config.apiServerUrl}
              onChange={(e) => setConfig({ ...config, apiServerUrl: e.target.value })}
            />
            <p className="text-xs text-muted-foreground">FastAPI 서버의 URL을 입력하세요</p>
          </div>

          <div className="space-y-2 rounded-lg border p-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">시스템 상태</span>
              <Button variant="outline" size="sm" onClick={checkAllStatus}>
                확인
              </Button>
            </div>
            <div className="space-y-2 pt-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">API 서버:</span>
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
                  <span className="text-muted-foreground">확인 중...</span>
                )}
              </div>
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Dify 연결:</span>
                {difyStatus ? (
                  <div className="flex items-center gap-2">
                    {difyStatus.connected ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span 
                      className={difyStatus.connected ? "text-green-500" : "text-red-500"}
                      style={{ whiteSpace: "pre-line", wordBreak: "break-word" }}
                    >
                      {difyStatus.message}
                    </span>
                  </div>
                ) : (
                  <span className="text-muted-foreground">-</span>
                )}
              </div>
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

