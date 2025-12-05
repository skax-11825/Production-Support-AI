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

    // 사용자가 입력한 URL을 그대로 사용 (수정하지 않음)
    console.log("[Dify Proxy] 요청 URL:", url)

    // Dify API 호출 (서버 사이드에서 실행되므로 CORS 문제 없음)
    // 브라우저처럼 보이도록 User-Agent 추가 (일부 서버가 User-Agent를 체크할 수 있음)
    const response = await fetch(url, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
      },
      body: JSON.stringify(payload),
    })

    const responseText = await response.text()
    
    console.log("[Dify Proxy] 응답 상태:", response.status, response.statusText)
    console.log("[Dify Proxy] 응답 본문 (처음 200자):", responseText.substring(0, 200))
    
    // HTML 응답인지 확인 (Ngrok 경고 페이지 또는 에러 페이지)
    if (responseText.trim().startsWith("<!DOCTYPE") || responseText.trim().startsWith("<html")) {
      console.error("[Dify Proxy] HTML 응답 감지 - Dify 서버 URL이 잘못되었거나 인증 문제일 수 있습니다.")
      return NextResponse.json(
        { 
          error: "Dify 서버에서 HTML 페이지를 반환했습니다. 다음을 확인하세요: 1) Dify API Base URL이 올바른지 확인 (예: https://your-dify.com 또는 https://your-dify.com/v1) 2) API Key가 유효한지 확인 3) Dify 서버가 정상 작동 중인지 확인 4) URL 끝에 쉼표(,)나 불필요한 문자가 없는지 확인"
        },
        { status: 500 }
      )
    }

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`
      try {
        const errorData = JSON.parse(responseText)
        errorMessage = errorData.message || errorData.error || errorMessage
        
        // Dify API 특정 에러 메시지 처리
        if (response.status === 401) {
          errorMessage = "인증 실패: API Key가 올바르지 않거나 만료되었습니다. Dify에서 새로운 API Key를 발급받으세요."
        } else if (response.status === 403) {
          errorMessage = "권한 없음: 이 API Key로는 해당 작업을 수행할 권한이 없습니다."
        } else if (response.status === 404) {
          errorMessage = "API 엔드포인트를 찾을 수 없습니다. Dify API Base URL이 올바른지 확인하세요. (예: https://your-dify.com/v1)"
        } else if (response.status === 500) {
          errorMessage = "Dify 서버 오류: Dify 서버에 문제가 있습니다. 잠시 후 다시 시도하세요."
        }
        
        console.error("[Dify Proxy] Dify API 오류:", errorMessage, errorData)
        return NextResponse.json(
          { error: errorMessage },
          { status: response.status }
        )
      } catch (parseError) {
        console.error("[Dify Proxy] JSON 파싱 실패:", parseError)
        return NextResponse.json(
          { error: `HTTP ${response.status}: ${response.statusText}. 응답: ${responseText.substring(0, 200)}` },
          { status: response.status }
        )
      }
    }

    const data = JSON.parse(responseText)
    return NextResponse.json(data)
  } catch (error) {
    console.error("[Dify Proxy] 예외 발생:", error)
    
    let errorMessage = "알 수 없는 오류가 발생했습니다."
    
    if (error instanceof TypeError) {
      if (error.message.includes("fetch")) {
        errorMessage = "네트워크 오류: Dify 서버에 연결할 수 없습니다. 다음을 확인하세요: 1) Dify 서버가 실행 중인지 확인 2) URL이 올바른지 확인 3) 방화벽이나 네트워크 설정 확인"
      } else {
        errorMessage = `네트워크 오류: ${error.message}`
      }
    } else if (error instanceof Error) {
      errorMessage = error.message
    }
    
    return NextResponse.json(
      { error: errorMessage },
      { status: 500 }
    )
  }
}

