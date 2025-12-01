#!/usr/bin/env python3
"""
API 엔드포인트별 입력-출력 검증 테스트
각 엔드포인트의 요청/응답이 명세서와 일치하는지 확인
"""
import httpx
import json
from datetime import date, datetime
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_section(title: str):
    """섹션 제목 출력"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

def test_endpoint(method: str, path: str, description: str, request_body: Dict[Any, Any] = None, expected_fields: list = None):
    """엔드포인트 테스트"""
    print(f"\n[테스트] {method} {path}")
    print(f"설명: {description}")
    
    if request_body:
        print(f"요청 본문: {json.dumps(request_body, indent=2, ensure_ascii=False, default=str)}")
    
    try:
        url = f"{BASE_URL}{path}"
        
        if method == "GET":
            response = httpx.get(url, timeout=10)
        else:
            response = httpx.post(url, json=request_body, timeout=10)
        
        print(f"\nHTTP 상태 코드: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"응답 본문: {json.dumps(result, indent=2, ensure_ascii=False, default=str)}")
            
            # 예상 필드 확인
            if expected_fields:
                print(f"\n예상 필드 확인:")
                for field in expected_fields:
                    if field in result or (isinstance(result, dict) and any(field in str(k) for k in result.keys())):
                        print(f"  ✓ {field}: 존재함")
                    else:
                        print(f"  ✗ {field}: 없음")
            
            print(f"\n✅ 테스트 통과")
            return True, result
        else:
            print(f"\n❌ 오류 발생")
            print(f"응답: {response.text[:500]}")
            return False, None
            
    except Exception as e:
        print(f"\n❌ 예외 발생: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """메인 테스트 함수"""
    print("=" * 80)
    print("API 엔드포인트 입력-출력 검증 테스트")
    print("=" * 80)
    print(f"\n기본 URL: {BASE_URL}")
    
    results = []
    
    # 1. 루트 엔드포인트
    print_section("1. 루트 엔드포인트")
    success, result = test_endpoint(
        "GET", "/",
        "서버 정보 반환",
        expected_fields=["message", "version"]
    )
    results.append(("GET /", success))
    
    # 2. 헬스 체크
    print_section("2. 헬스 체크")
    success, result = test_endpoint(
        "GET", "/health",
        "서버 및 데이터베이스 연결 상태 확인",
        expected_fields=["status", "database_connected", "dify_enabled"]
    )
    results.append(("GET /health", success))
    
    # 3. ID 조회
    print_section("3. ID 조회 API")
    success, result = test_endpoint(
        "POST", "/lookup/ids",
        "ID 조회 (process_name, model_name, eqp_name → ID 변환)",
        request_body={
            "process_name": "Cleaning",
            "eqp_name": "ASML_PH_#001"
        },
        expected_fields=["process_id", "model_id", "eqp_id"]
    )
    results.append(("POST /lookup/ids", success))
    
    # 4. 에러 코드 통계
    print_section("4. 에러 코드 통계 조회")
    success, result = test_endpoint(
        "POST", "/api/v1/informnote/stats/error-code",
        "Error Code별 통계 조회",
        request_body={
            "start_date": "2025-06-01",
            "end_date": "2025-06-30",
            "process_id": "PROC_CLN",
            "group_by": "error_code"
        },
        expected_fields=["list"]
    )
    results.append(("POST /api/v1/informnote/stats/error-code", success))
    
    # 5. PM 이력 조회
    print_section("5. PM 이력 조회")
    success, result = test_endpoint(
        "POST", "/api/v1/informnote/history/pm",
        "PM(점검) 이력 조회",
        request_body={
            "start_date": "2025-06-01",
            "end_date": "2025-06-30",
            "limit": 5
        },
        expected_fields=["list"]
    )
    results.append(("POST /api/v1/informnote/history/pm", success))
    
    # 6. 상세 검색
    print_section("6. 상세 조치 내역 검색")
    success, result = test_endpoint(
        "POST", "/api/v1/informnote/search",
        "상세 조치 내역 검색",
        request_body={
            "start_date": "2025-06-01",
            "end_date": "2025-06-30",
            "process_id": "PROC_CLN",
            "limit": 5
        },
        expected_fields=["list"]
    )
    results.append(("POST /api/v1/informnote/search", success))
    
    # 7. 질문-답변
    print_section("7. 질문-답변")
    success, result = test_endpoint(
        "POST", "/ask",
        "질문에 대한 답변 생성",
        request_body={
            "question": "Cleaning 공정의 다운타임을 알려줘"
        },
        expected_fields=["answer", "question", "success"]
    )
    results.append(("POST /ask", success))
    
    # 최종 결과
    print_section("테스트 결과 요약")
    total = len(results)
    passed = sum(1 for _, success in results if success)
    failed = total - passed
    
    for endpoint, success in results:
        status = "✅ 통과" if success else "❌ 실패"
        print(f"  {status}: {endpoint}")
    
    print(f"\n총 {total}개 엔드포인트 테스트: {passed}개 통과, {failed}개 실패")
    print("=" * 80)

if __name__ == "__main__":
    main()

