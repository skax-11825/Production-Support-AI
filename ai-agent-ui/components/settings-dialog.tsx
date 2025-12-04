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
      const response = await fetch(`${config.apiServerUrl}/health`)
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data = await response.json()
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
      setDifyStatus({ connected: false, message: "API Key가 설정되지 않았습니다." })
      return
    }

    try {
      const url = `${config.difyApiBase}/chat-messages`
      const response = await fetch(url, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${config.difyApiKey}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          inputs: {},
          query: "테스트",
          response_mode: "blocking",
          user: "web-ui-user",
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || `HTTP ${response.status}`)
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
                    <span className={difyStatus.connected ? "text-green-500" : "text-red-500"}>
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

