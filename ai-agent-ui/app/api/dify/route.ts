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
    // 모든 종류의 공백 문자 제거 (공백, 탭, 줄바꿈 등)
    const rawApiKey = (apiKey || "").toString()
    const trimmedApiKey = rawApiKey.trim()
    const cleanApiKey = trimmedApiKey.replace(/\s+/g, "") // 모든 공백 제거
    
    console.log("[Dify Proxy] 요청 URL:", url)
    console.log("[Dify Proxy] 원본 API Key 길이:", rawApiKey.length)
    console.log("[Dify Proxy] 정리 후 API Key 길이:", cleanApiKey.length)
    console.log("[Dify Proxy] API Key 시작:", cleanApiKey.length > 0 ? cleanApiKey.substring(0, Math.min(10, cleanApiKey.length)) + "..." : "EMPTY")
    console.log("[Dify Proxy] API Key 끝:", cleanApiKey.length > 10 ? "..." + cleanApiKey.substring(cleanApiKey.length - 5) : cleanApiKey)
    
    if (!trimmedApiKey || !cleanApiKey) {
      console.error("[Dify Proxy] API Key가 비어있습니다.")
      return NextResponse.json(
        { error: "API Key가 비어있습니다. Dify API Key를 입력하세요." },
        { status: 400, headers: corsHeaders }
      )
    }

    // API Key 형식 검증 (일반적으로 app- 또는 sk-로 시작)
    if (cleanApiKey.length < 10) {
      console.error("[Dify Proxy] API Key가 너무 짧습니다:", cleanApiKey.length)
      return NextResponse.json(
        { error: "API Key가 올바르지 않습니다. Dify에서 발급받은 API Key를 확인하세요." },
        { status: 400, headers: corsHeaders }
      )
    }

    // Authorization 헤더 생성 및 검증
    // Dify API는 Bearer 토큰 형식을 사용
    const authHeader = `Bearer ${cleanApiKey}`
    console.log("[Dify Proxy] Authorization 헤더 생성됨 (처음 30자):", authHeader.substring(0, 30) + "...")
    console.log("[Dify Proxy] Authorization 헤더 전체 길이:", authHeader.length)
    
    // Authorization 헤더 형식 검증
    if (!authHeader.startsWith("Bearer ") || authHeader.length < 15) {
      console.error("[Dify Proxy] Authorization 헤더 형식이 올바르지 않습니다:", authHeader.substring(0, 30))
      return NextResponse.json(
        { error: "API Key 형식이 올바르지 않습니다. Dify에서 발급받은 API Key를 확인하세요." },
        { status: 400, headers: corsHeaders }
      )
    }
    
    // URL 정리 및 검증
    const cleanUrl = url.trim()
    if (!cleanUrl || !cleanUrl.startsWith("http")) {
      console.error("[Dify Proxy] URL이 올바르지 않습니다:", cleanUrl)
      return NextResponse.json(
        { error: "Dify API Base URL이 올바르지 않습니다. http:// 또는 https://로 시작하는 URL을 입력하세요." },
        { status: 400, headers: corsHeaders }
      )
    }

    // Dify API 호출 (서버 사이드에서 실행되므로 CORS 문제 없음)
    // Dify API는 표준 Bearer 토큰 인증을 사용
    const requestHeaders: Record<string, string> = {
      "Authorization": authHeader,
      "Content-Type": "application/json",
      "Accept": "application/json",
    }
    
    console.log("[Dify Proxy] 최종 요청 정보:")
    console.log("  - URL:", cleanUrl)
    console.log("  - Authorization 헤더 (처음 30자):", authHeader.substring(0, 30) + "...")
    console.log("  - Authorization 헤더 전체 길이:", authHeader.length)
    console.log("  - Content-Type:", requestHeaders["Content-Type"])
    console.log("  - Payload 크기:", JSON.stringify(payload).length, "bytes")
    
    const response = await fetch(cleanUrl, {
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
          const difyErrorMsg = (errorData.message || errorData.error || errorData.code || "").toLowerCase()
          const fullErrorMsg = errorData.message || errorData.error || JSON.stringify(errorData)
          
          console.error("[Dify Proxy] 401 에러 상세:")
          console.error("  - 에러 메시지:", fullErrorMsg)
          console.error("  - 에러 코드:", errorData.code || "N/A")
          console.error("  - 사용된 URL:", cleanUrl)
          console.error("  - Authorization 헤더 (처음 30자):", authHeader.substring(0, 30) + "...")
          console.error("  - API Key 길이:", cleanApiKey.length)
          
          if (difyErrorMsg.includes("authorization") || difyErrorMsg.includes("bearer") || difyErrorMsg.includes("token")) {
            errorMessage = "인증 실패: Authorization 헤더가 올바르지 않습니다. API Key를 확인하세요.\n\n해결 방법:\n1. Dify에서 새로운 API Key를 발급받으세요\n2. API Key에 공백이나 특수문자가 없는지 확인하세요\n3. API Key를 복사할 때 앞뒤 공백이 포함되지 않았는지 확인하세요"
          } else if (difyErrorMsg.includes("invalid") || difyErrorMsg.includes("expired") || difyErrorMsg.includes("unauthorized")) {
            errorMessage = "인증 실패: API Key가 올바르지 않거나 만료되었습니다.\n\n해결 방법:\n1. Dify에서 새로운 API Key를 발급받으세요\n2. API Key가 활성화되어 있는지 확인하세요\n3. API Key가 해당 애플리케이션에 연결되어 있는지 확인하세요"
          } else if (difyErrorMsg.includes("ip") || difyErrorMsg.includes("domain") || difyErrorMsg.includes("whitelist") || difyErrorMsg.includes("forbidden")) {
            errorMessage = "인증 실패: Dify 서버가 특정 IP나 도메인만 허용하도록 설정되어 있습니다.\n\n해결 방법:\n1. Dify 서버 관리자에게 현재 서버 IP를 허용 목록에 추가해달라고 요청하세요\n2. 또는 Dify 서버의 IP 화이트리스트 설정을 확인하세요"
          } else {
            errorMessage = `인증 실패: ${fullErrorMsg}\n\n해결 방법:\n1. Dify API Base URL이 올바른지 확인하세요 (예: http://your-server.com/v1)\n2. API Key가 올바른지 확인하세요\n3. Dify 서버가 실행 중인지 확인하세요`
          }
        } else if (response.status === 403) {
          errorMessage = "권한 없음: 이 API Key로는 해당 작업을 수행할 권한이 없습니다.\n\n해결 방법:\n1. API Key에 필요한 권한이 있는지 확인하세요\n2. Dify 서버가 특정 IP/도메인만 허용하도록 설정되어 있을 수 있습니다"
        } else if (response.status === 404) {
          errorMessage = "API 엔드포인트를 찾을 수 없습니다.\n\n해결 방법:\n1. Dify API Base URL이 올바른지 확인하세요 (예: http://your-server.com/v1)\n2. URL 끝에 /v1이 포함되어 있는지 확인하세요\n3. 엔드포인트 경로가 올바른지 확인하세요 (/chat-messages)"
        } else if (response.status === 500) {
          errorMessage = "Dify 서버 오류: Dify 서버에 문제가 있습니다.\n\n해결 방법:\n1. 잠시 후 다시 시도하세요\n2. Dify 서버 로그를 확인하세요\n3. Dify 서버 관리자에게 문의하세요"
        }
        
        console.error("[Dify Proxy] Dify API 오류:", errorMessage)
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

