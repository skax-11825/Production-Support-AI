import { NextRequest, NextResponse } from "next/server"

// CORS 헤더 설정 (하드코딩)
const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
  "Access-Control-Max-Age": "86400",
}

export async function OPTIONS(request: NextRequest) {
  return NextResponse.json({}, { headers: corsHeaders })
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { url, apiKey, payload } = body

    if (!url || !apiKey) {
      return NextResponse.json(
        { error: "URL and API Key are required" },
        { status: 400, headers: corsHeaders }
      )
    }

    // API Key 검증 및 로깅 (보안상 전체는 로깅하지 않음)
    const trimmedApiKey = (apiKey || "").trim()
    console.log("[Dify Proxy] 요청 URL:", url)
    console.log("[Dify Proxy] API Key 길이:", trimmedApiKey.length)
    console.log("[Dify Proxy] API Key 시작:", trimmedApiKey.length > 0 ? trimmedApiKey.substring(0, Math.min(10, trimmedApiKey.length)) + "..." : "EMPTY")
    
    if (!trimmedApiKey) {
      console.error("[Dify Proxy] API Key가 비어있습니다.")
      return NextResponse.json(
        { error: "API Key가 비어있습니다. Dify API Key를 입력하세요." },
        { status: 400 }
      )
    }

    // Authorization 헤더 생성 및 검증
    // API Key에 특수문자가 있는지 확인하고 인코딩
    const cleanApiKey = trimmedApiKey.replace(/\s+/g, "") // 모든 공백 제거
    if (!cleanApiKey) {
      console.error("[Dify Proxy] API Key가 공백만 있습니다.")
      return NextResponse.json(
        { error: "API Key가 올바르지 않습니다. 공백 없이 입력하세요." },
        { status: 400, headers: corsHeaders }
      )
    }
    
    const authHeader = `Bearer ${cleanApiKey}`
    console.log("[Dify Proxy] Authorization 헤더 생성됨:", authHeader.substring(0, 25) + "...")
    console.log("[Dify Proxy] API Key 정리 후 길이:", cleanApiKey.length)
    
    // Authorization 헤더 형식 검증
    if (!authHeader.startsWith("Bearer ") || authHeader.length < 15) {
      console.error("[Dify Proxy] Authorization 헤더 형식이 올바르지 않습니다:", authHeader.substring(0, 30))
      return NextResponse.json(
        { error: "API Key 형식이 올바르지 않습니다. Dify에서 발급받은 API Key를 확인하세요." },
        { status: 400, headers: corsHeaders }
      )
    }
    
    // 사용자가 입력한 URL을 그대로 사용 (수정하지 않음)

    // Dify API 호출 (서버 사이드에서 실행되므로 CORS 문제 없음)
    // 브라우저처럼 보이도록 User-Agent 추가 (일부 서버가 User-Agent를 체크할 수 있음)
    const requestHeaders: Record<string, string> = {
      "Authorization": authHeader,
      "Content-Type": "application/json",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
      "Accept": "application/json",
    }
    
    console.log("[Dify Proxy] 요청 헤더 (요약):", {
      "Authorization": authHeader.substring(0, 25) + "...",
      "Content-Type": requestHeaders["Content-Type"],
      "User-Agent": requestHeaders["User-Agent"].substring(0, 50) + "...",
      "Accept": requestHeaders["Accept"],
    })
    console.log("[Dify Proxy] Authorization 헤더 전체 길이:", authHeader.length)
    
    const response = await fetch(url, {
      method: "POST",
      headers: requestHeaders,
      body: JSON.stringify(payload),
    })

    const responseText = await response.text()
    
    console.log("[Dify Proxy] 응답 상태:", response.status, response.statusText)
    console.log("[Dify Proxy] 응답 본문 (처음 500자):", responseText.substring(0, 500))
    console.log("[Dify Proxy] 응답 헤더:", Object.fromEntries(response.headers.entries()))
    
    // HTML 응답인지 확인 (Ngrok 경고 페이지 또는 에러 페이지)
    if (responseText.trim().startsWith("<!DOCTYPE") || responseText.trim().startsWith("<html")) {
      console.error("[Dify Proxy] HTML 응답 감지")
      console.error("[Dify Proxy] 상태 코드:", response.status)
      console.error("[Dify Proxy] 응답 URL:", url)
      
      // 상태 코드에 따른 더 구체적인 메시지
      let errorMsg = "Dify 서버에서 HTML 페이지를 반환했습니다."
      if (response.status === 403) {
        errorMsg += " 접근이 거부되었습니다. Dify 서버가 특정 IP나 도메인만 허용하도록 설정되어 있을 수 있습니다. Azure 방화벽이나 Dify 서버 설정을 확인하세요."
      } else if (response.status === 404) {
        errorMsg += " 요청한 엔드포인트를 찾을 수 없습니다. Dify API Base URL이 올바른지 확인하세요."
      } else if (response.status === 401) {
        errorMsg += " 인증이 실패했습니다. API Key가 올바른지 확인하세요."
      } else {
        errorMsg += " Dify 서버 설정이나 네트워크 접근 권한을 확인하세요."
      }
      
      return NextResponse.json(
        { 
          error: errorMsg
        },
        { status: response.status || 500, headers: corsHeaders }
      )
    }

    if (!response.ok) {
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`
      try {
        const errorData = JSON.parse(responseText)
        errorMessage = errorData.message || errorData.error || errorMessage
        
        // Dify API 특정 에러 메시지 처리
        if (response.status === 401) {
          // Dify 서버의 실제 에러 메시지 확인
          const difyErrorMsg = (errorData.message || errorData.error || "").toLowerCase()
          console.error("[Dify Proxy] 401 에러 상세:", difyErrorMsg)
          
          if (difyErrorMsg.includes("authorization header") || difyErrorMsg.includes("bearer")) {
            errorMessage = "인증 실패: Authorization 헤더가 올바르지 않습니다. API Key를 확인하세요."
          } else if (difyErrorMsg.includes("invalid") || difyErrorMsg.includes("expired")) {
            errorMessage = "인증 실패: API Key가 올바르지 않거나 만료되었습니다. Dify에서 새로운 API Key를 발급받으세요."
          } else if (difyErrorMsg.includes("ip") || difyErrorMsg.includes("domain") || difyErrorMsg.includes("whitelist")) {
            errorMessage = "인증 실패: Dify 서버가 특정 IP나 도메인만 허용하도록 설정되어 있습니다. Dify 서버 관리자에게 Vercel 서버 IP를 허용 목록에 추가해달라고 요청하세요."
          } else {
            errorMessage = `인증 실패: ${errorData.message || errorData.error || "API Key가 올바르지 않거나 만료되었습니다. Dify에서 새로운 API Key를 발급받으세요."}`
          }
        } else if (response.status === 403) {
          errorMessage = "권한 없음: 이 API Key로는 해당 작업을 수행할 권한이 없습니다. 또는 Dify 서버가 특정 IP/도메인만 허용하도록 설정되어 있을 수 있습니다."
        } else if (response.status === 404) {
          errorMessage = "API 엔드포인트를 찾을 수 없습니다. Dify API Base URL이 올바른지 확인하세요. (예: https://your-dify.com/v1)"
        } else if (response.status === 500) {
          errorMessage = "Dify 서버 오류: Dify 서버에 문제가 있습니다. 잠시 후 다시 시도하세요."
        }
        
        console.error("[Dify Proxy] Dify API 오류:", errorMessage, errorData)
        console.error("[Dify Proxy] 사용된 Authorization 헤더:", authHeader.substring(0, 30) + "...")
        return NextResponse.json(
          { error: errorMessage },
          { status: response.status, headers: corsHeaders }
        )
      } catch (parseError) {
        console.error("[Dify Proxy] JSON 파싱 실패:", parseError)
        return NextResponse.json(
          { error: `HTTP ${response.status}: ${response.statusText}. 응답: ${responseText.substring(0, 200)}` },
          { status: response.status, headers: corsHeaders }
        )
      }
    }

    const data = JSON.parse(responseText)
    console.log("[Dify Proxy] 성공 응답 받음")
    return NextResponse.json(data, { headers: corsHeaders })
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
      { status: 500, headers: corsHeaders }
    )
  }
}

