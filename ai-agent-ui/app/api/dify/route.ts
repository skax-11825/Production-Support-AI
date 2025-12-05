import { NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { url, apiKey, payload } = body

    if (!url || !apiKey) {
      return NextResponse.json(
        { error: "URL and API Key are required" },
        { status: 400 }
      )
    }

    // Dify API 호출 (서버 사이드에서 실행되므로 CORS 문제 없음)
    const response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })

    const responseText = await response.text()
    
    // HTML 응답인지 확인 (Ngrok 경고 페이지 또는 에러 페이지)
    if (responseText.trim().startsWith("<!DOCTYPE") || responseText.trim().startsWith("<html")) {
      return NextResponse.json(
        { error: "Dify 서버에서 HTML 페이지를 반환했습니다. URL이 올바른지 확인하세요." },
        { status: 500 }
      )
    }

    if (!response.ok) {
      try {
        const errorData = JSON.parse(responseText)
        return NextResponse.json(
          { error: errorData.message || errorData.error || `HTTP ${response.status}: ${response.statusText}` },
          { status: response.status }
        )
      } catch {
        return NextResponse.json(
          { error: `HTTP ${response.status}: ${response.statusText}` },
          { status: response.status }
        )
      }
    }

    const data = JSON.parse(responseText)
    return NextResponse.json(data)
  } catch (error) {
    console.error("[Dify Proxy] 오류:", error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 500 }
    )
  }
}

