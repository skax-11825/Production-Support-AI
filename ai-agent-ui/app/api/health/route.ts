import { NextRequest, NextResponse } from "next/server"

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const apiServerUrl = searchParams.get("url")

    if (!apiServerUrl) {
      return NextResponse.json(
        { error: "URL parameter is required" },
        { status: 400 }
      )
    }

    // API 서버 헬스 체크 (서버 사이드에서 실행되므로 CORS 문제 없음)
    const response = await fetch(`${apiServerUrl}/health`, {
      headers: {
        "ngrok-skip-browser-warning": "true",
      },
    })

    if (!response.ok) {
      const errorText = await response.text()
      return NextResponse.json(
        { error: errorText },
        { status: response.status }
      )
    }

    const text = await response.text()
    
    // HTML 응답인지 확인
    if (text.trim().startsWith("<!DOCTYPE") || text.trim().startsWith("<html")) {
      return NextResponse.json(
        { error: "HTML response received (possibly Ngrok warning page)" },
        { status: 500 }
      )
    }

    const data = JSON.parse(text)
    return NextResponse.json(data)
  } catch (error) {
    console.error("[Health Check Proxy] 오류:", error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    )
  }
}

