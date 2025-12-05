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
    // 끝의 쉼표, 세미콜론, 공백 제거
    let cleanUrl = url.trim().replace(/[,;\s]+$/, "")
    
    if (!cleanUrl || !cleanUrl.startsWith("http")) {
      console.error("[Dify Proxy] URL이 올바르지 않습니다:", cleanUrl)
      return NextResponse.json(
        { error: "Dify API Base URL이 올바르지 않습니다. http:// 또는 https://로 시작하는 URL을 입력하세요." },
        { status: 400, headers: corsHeaders }
      )
    }
    
    // 이미 chat-messages 경로가 포함되어 있으면 그대로 사용
    // 그렇지 않으면 URL 정리 후 경로 추가
    if (!cleanUrl.includes("/chat-messages")) {
      // 끝의 슬래시 제거 (경로 추가 전)
      cleanUrl = cleanUrl.replace(/\/+$/, "")
      
      // /v1 경로가 없으면 자동 추가 (일부 Dify 서버는 /v1이 필요함)
      // 단, 포트 번호가 있거나 이미 경로가 있으면 그대로 사용
      if (!cleanUrl.match(/\/v\d+$/) && !cleanUrl.match(/:\d+\//)) {
        // 포트 번호가 있고 경로가 없는 경우에만 /v1 추가
        if (cleanUrl.match(/:\d+$/)) {
          cleanUrl = `${cleanUrl}/v1`
        } else if (!cleanUrl.includes("/", 8)) { // 프로토콜 부분 이후에 슬래시가 없으면
          cleanUrl = `${cleanUrl}/v1`
        }
      }
      
      // chat-messages 경로 추가
      cleanUrl = `${cleanUrl}/chat-messages`
    }
    
    console.log("[Dify Proxy] URL 정리 완료:")
    console.log("  - 원본 URL:", url)
    console.log("  - 정리된 URL:", cleanUrl)

    // Dify API 호출 (서버 사이드에서 실행되므로 CORS 문제 없음)
    // Dify API는 표준 Bearer 토큰 인증을 사용
    // 참고: 일부 Dify 서버는 다른 헤더 형식을 요구할 수 있음
    const requestHeaders: Record<string, string> = {
      "Authorization": authHeader,
      "Content-Type": "application/json",
      "Accept": "application/json",
    }
    
    // 추가 헤더 (일부 Dify 서버가 요구할 수 있음)
    // User-Agent를 추가하여 일부 서버의 차단을 우회
    requestHeaders["User-Agent"] = "Dify-Client/1.0"
    
    console.log("[Dify Proxy] ========== 요청 정보 ==========")
    console.log("  - URL:", cleanUrl)
    console.log("  - Method: POST")
    console.log("  - Authorization 헤더 (마스킹):", authHeader.substring(0, 15) + "..." + authHeader.substring(authHeader.length - 5))
    console.log("  - Authorization 헤더 전체 길이:", authHeader.length)
    console.log("  - Content-Type:", requestHeaders["Content-Type"])
    console.log("  - Accept:", requestHeaders["Accept"])
    console.log("  - User-Agent:", requestHeaders["User-Agent"])
    console.log("  - Payload:", JSON.stringify(payload, null, 2))
    console.log("  - Payload 크기:", JSON.stringify(payload).length, "bytes")
    console.log("  =========================================")
    
    const response = await fetch(cleanUrl, {
      method: "POST",
      headers: requestHeaders,
      body: JSON.stringify(payload),
    })

    const responseText = await response.text()
    
    console.log("[Dify Proxy] ========== 응답 상세 정보 ==========")
    console.log("[Dify Proxy] 응답 상태:", response.status, response.statusText)
    console.log("[Dify Proxy] 응답 본문 (전체):", responseText)
    console.log("[Dify Proxy] 응답 본문 길이:", responseText.length)
    console.log("[Dify Proxy] 응답 헤더:", Object.fromEntries(response.headers.entries()))
    console.log("[Dify Proxy] 요청 URL:", cleanUrl)
    console.log("[Dify Proxy] Authorization 헤더 (마스킹):", authHeader.substring(0, 15) + "..." + authHeader.substring(authHeader.length - 5))
    console.log("[Dify Proxy] ====================================")
    
    // HTML 응답인지 확인 (Ngrok 경고 페이지 또는 에러 페이지)
    if (responseText.trim().startsWith("<!DOCTYPE") || responseText.trim().startsWith("<html") || responseText.trim().startsWith("<!doctype")) {
      console.error("[Dify Proxy] HTML 응답 감지")
      console.error("[Dify Proxy] 상태 코드:", response.status)
      console.error("[Dify Proxy] 응답 URL:", cleanUrl)
      console.error("[Dify Proxy] HTML 응답 (처음 1000자):", responseText.substring(0, 1000))
      
      // 상태 코드에 따른 더 구체적인 메시지
      let errorMsg = "Dify 서버에서 HTML 페이지를 반환했습니다."
      let suggestions = []
      
      if (response.status === 403) {
        errorMsg += " 접근이 거부되었습니다."
        suggestions.push("Dify 서버가 특정 IP나 도메인만 허용하도록 설정되어 있을 수 있습니다.")
        suggestions.push("Azure 방화벽이나 Dify 서버 설정을 확인하세요.")
      } else if (response.status === 404) {
        errorMsg += " 요청한 엔드포인트를 찾을 수 없습니다."
        suggestions.push("Dify API Base URL이 올바른지 확인하세요.")
        suggestions.push("URL 형식: https://your-server.com:포트/v1 또는 https://your-server.com/v1")
        suggestions.push("포트 번호가 있는 경우 URL 끝에 쉼표가 없는지 확인하세요.")
        suggestions.push("일부 Dify 서버는 /v1 경로가 필요합니다.")
        
        // URL에 문제가 있을 수 있는 경우 제안
        if (cleanUrl.includes(":3000")) {
          suggestions.push("포트 3000이 올바른지 확인하세요. Dify 기본 포트는 보통 80 또는 443입니다.")
        }
        if (!cleanUrl.includes("/v1") && !cleanUrl.includes("/chat-messages")) {
          suggestions.push("URL에 /v1 경로가 포함되어 있는지 확인하세요.")
        }
      } else if (response.status === 401) {
        errorMsg += " 인증이 실패했습니다."
        suggestions.push("API Key가 올바른지 확인하세요.")
      } else {
        errorMsg += " Dify 서버 설정이나 네트워크 접근 권한을 확인하세요."
      }
      
      if (suggestions.length > 0) {
        errorMsg += "\n\n해결 방법:\n" + suggestions.map((s, i) => `${i + 1}. ${s}`).join("\n")
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
          
          console.error("[Dify Proxy] ========== 401 인증 실패 상세 분석 ==========")
          console.error("  - 전체 에러 응답:", JSON.stringify(errorData, null, 2))
          console.error("  - 에러 메시지:", fullErrorMsg)
          console.error("  - 에러 코드:", errorData.code || "N/A")
          console.error("  - 사용된 URL:", cleanUrl)
          console.error("  - API Key 길이:", cleanApiKey.length)
          console.error("  - API Key 시작:", cleanApiKey.substring(0, 10) + "...")
          console.error("  - API Key 끝:", "..." + cleanApiKey.substring(cleanApiKey.length - 5))
          console.error("  - Authorization 헤더 (마스킹):", authHeader.substring(0, 15) + "..." + authHeader.substring(authHeader.length - 5))
          console.error("  - Authorization 헤더 전체 길이:", authHeader.length)
          console.error("  - Payload:", JSON.stringify(payload, null, 2))
          console.error("  =========================================================")
          
          // 가능한 원인별 상세 메시지
          if (difyErrorMsg.includes("authorization") || difyErrorMsg.includes("bearer") || difyErrorMsg.includes("token") || difyErrorMsg.includes("header")) {
            errorMessage = "인증 실패: Authorization 헤더가 올바르지 않습니다.\n\n가능한 원인:\n1. API Key 형식이 잘못되었을 수 있습니다\n2. Authorization 헤더 형식이 Dify 서버가 기대하는 것과 다를 수 있습니다\n3. API Key에 보이지 않는 특수문자가 포함되어 있을 수 있습니다\n\n해결 방법:\n1. Dify 대시보드에서 새로운 API Key를 발급받으세요\n2. API Key를 직접 복사-붙여넣기하세요 (수동 입력 금지)\n3. API Key 앞뒤 공백을 확인하세요\n4. Dify 서버가 자체 호스팅인 경우 인증 방식이 다를 수 있습니다"
          } else if (difyErrorMsg.includes("invalid") || difyErrorMsg.includes("expired") || difyErrorMsg.includes("unauthorized") || difyErrorMsg.includes("app unavailable")) {
            errorMessage = "인증 실패: API Key가 올바르지 않거나 앱이 게시되지 않았습니다.\n\n가능한 원인:\n1. API Key가 만료되었거나 삭제되었습니다\n2. Dify 애플리케이션이 '게시(Published)' 상태가 아닙니다\n3. API Key가 다른 애플리케이션에 연결되어 있습니다\n4. 워크플로우가 게시되지 않았습니다\n\n해결 방법:\n1. Dify 대시보드에서 애플리케이션이 '게시' 상태인지 확인하세요\n2. 워크플로우가 게시되었는지 확인하세요\n3. 새로운 API Key를 발급받으세요\n4. API Key가 올바른 애플리케이션에 연결되어 있는지 확인하세요"
          } else if (difyErrorMsg.includes("ip") || difyErrorMsg.includes("domain") || difyErrorMsg.includes("whitelist") || difyErrorMsg.includes("forbidden") || difyErrorMsg.includes("cors")) {
            errorMessage = "인증 실패: Dify 서버의 접근 제한 설정 문제입니다.\n\n가능한 원인:\n1. Dify 서버가 특정 IP나 도메인만 허용하도록 설정되어 있습니다\n2. Vercel 서버의 IP가 화이트리스트에 없습니다\n3. CORS 설정이 올바르지 않습니다\n4. Azure 방화벽이 요청을 차단하고 있습니다\n\n해결 방법:\n1. Dify 서버 관리자에게 Vercel IP 범위를 허용 목록에 추가해달라고 요청하세요\n2. Azure 방화벽 설정에서 Vercel IP를 허용하세요\n3. Dify 서버의 CORS 설정을 확인하세요\n4. 임시로 IP 제한을 해제하고 테스트해보세요"
          } else if (difyErrorMsg.includes("workflow") || difyErrorMsg.includes("not published")) {
            errorMessage = "인증 실패: 워크플로우가 게시되지 않았습니다.\n\n가능한 원인:\n1. 사용 중인 워크플로우가 게시되지 않았습니다\n2. 워크플로우에 오류가 있습니다\n\n해결 방법:\n1. Dify 대시보드에서 워크플로우를 게시하세요\n2. 워크플로우에 오류가 없는지 확인하세요"
          } else {
            errorMessage = `인증 실패: ${fullErrorMsg}\n\n가능한 원인:\n1. Dify API Base URL이 올바르지 않을 수 있습니다\n2. API Key가 올바르지 않거나 만료되었을 수 있습니다\n3. Dify 서버 설정 문제일 수 있습니다\n4. 네트워크 연결 문제일 수 있습니다\n\n해결 방법:\n1. Dify API Base URL이 올바른지 확인하세요 (예: http://your-server.com/v1)\n2. URL 끝에 /v1이 포함되어 있는지 확인하세요\n3. Dify 서버가 실행 중인지 확인하세요\n4. 브라우저 개발자 도구의 네트워크 탭에서 실제 요청을 확인하세요\n5. Dify 서버 로그를 확인하세요`
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

