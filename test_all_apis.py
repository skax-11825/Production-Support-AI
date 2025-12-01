#!/usr/bin/env python3
"""
모든 API 엔드포인트 종합 테스트 스크립트
입력값 대비 출력값 검증 및 품질 개선
"""
import httpx
import json
from datetime import date
from typing import Dict, Any, List
import sys

BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0
test_results = []

def print_header(title: str):
    """테스트 섹션 헤더 출력"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_test(name: str, request_data: Dict = None):
    """테스트 시작 출력"""
    print(f"\n[테스트] {name}")
    if request_data:
        print(f"  요청: {json.dumps(request_data, indent=2, ensure_ascii=False, default=str)}")

def test_result(success: bool, message: str, response_data: Any = None):
    """테스트 결과 기록"""
    status = "✓ 성공" if success else "✗ 실패"
    print(f"  {status}: {message}")
    if response_data:
        data_str = json.dumps(response_data, indent=2, ensure_ascii=False, default=str)
        if len(data_str) > 200:
            data_str = data_str[:200] + "..."
        print(f"  응답: {data_str}")
    test_results.append({
        "success": success,
        "message": message
    })

async def test_root(client: httpx.AsyncClient):
    """GET / - 루트 엔드포인트 테스트"""
    print_header("1. GET / - 루트 엔드포인트")
    
    try:
        response = await client.get("/", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "version" in data:
                test_result(True, "루트 엔드포인트 정상 응답", data)
            else:
                test_result(False, "응답 형식이 올바르지 않음", data)
        else:
            test_result(False, f"HTTP {response.status_code} 오류: {response.text[:200]}")
    except Exception as e:
        test_result(False, f"예외 발생: {str(e)}")

async def test_health(client: httpx.AsyncClient):
    """GET /health - 헬스체크 테스트"""
    print_header("2. GET /health - 헬스체크")
    
    try:
        response = await client.get("/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            required_fields = ["status", "database_connected", "dify_enabled"]
            if all(field in data for field in required_fields):
                status_ok = data["status"] == "healthy" and data["database_connected"]
                test_result(status_ok, f"헬스체크 정상 (DB: {data['database_connected']}, Dify: {data['dify_enabled']})", data)
            else:
                test_result(False, "필수 필드 누락", data)
        else:
            test_result(False, f"HTTP {response.status_code} 오류: {response.text[:200]}")
    except Exception as e:
        test_result(False, f"예외 발생: {str(e)}")

async def test_lookup_ids(client: httpx.AsyncClient):
    """POST /lookup/ids - ID 조회 테스트"""
    print_header("3. POST /lookup/ids - ID 조회")
    
    test_cases = [
        {
            "name": "process_name만 입력 (Cleaning)",
            "data": {"process_name": "Cleaning"},
            "expected": lambda d: d.get("process_id") is not None
        },
        {
            "name": "process_name 부분 일치 (Clean)",
            "data": {"process_name": "Clean"},
            "expected": lambda d: d.get("process_id") is not None
        },
        {
            "name": "process_name 대소문자 혼합 (PHOTOLITHOGRAPHY)",
            "data": {"process_name": "PHOTOLITHOGRAPHY"},
            "expected": lambda d: d.get("process_id") is not None
        },
        {
            "name": "모든 필드 입력",
            "data": {
                "process_name": "Cleaning",
                "model_name": "Lam",
                "eqp_name": "CLN"
            },
            "expected": lambda d: d.get("process_id") is not None or d.get("model_id") is not None or d.get("eqp_id") is not None
        },
        {
            "name": "빈 요청",
            "data": {},
            "expected": lambda d: True  # 빈 요청은 항상 성공 (모두 null 반환)
        },
        {
            "name": "존재하지 않는 값",
            "data": {"process_name": "NonExistentProcess12345"},
            "expected": lambda d: d.get("process_id") is None  # null이어야 함
        }
    ]
    
    for test_case in test_cases:
        print_test(test_case["name"], test_case["data"])
        try:
            response = await client.post("/lookup/ids", json=test_case["data"], timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["process_id", "model_id", "eqp_id"]
                
                if all(field in data for field in required_fields):
                    success = test_case["expected"](data)
                    test_result(success, f"ID 조회 {'성공' if success else '실패'}: process_id={data.get('process_id')}", data)
                else:
                    test_result(False, "필수 필드 누락", data)
            else:
                test_result(False, f"HTTP {response.status_code} 오류: {response.text[:200]}")
        except Exception as e:
            test_result(False, f"예외 발생: {str(e)}")

async def test_error_stats(client: httpx.AsyncClient):
    """POST /api/v1/informnote/stats/error-code - 에러 통계 조회 테스트"""
    print_header("4. POST /api/v1/informnote/stats/error-code - 에러 통계 조회")
    
    test_cases = [
        {
            "name": "빈 요청 (전체 통계)",
            "data": {},
            "expected": lambda d: "list" in d and isinstance(d["list"], list)
        },
        {
            "name": "날짜 범위 지정",
            "data": {
                "start_date": "2025-01-01",
                "end_date": "2025-12-31"
            },
            "expected": lambda d: "list" in d and isinstance(d["list"], list)
        },
        {
            "name": "프로세스 필터링",
            "data": {"process_id": "PROC_CLN"},
            "expected": lambda d: "list" in d and isinstance(d["list"], list)
        },
        {
            "name": "월별 집계",
            "data": {
                "process_id": "PROC_PH",
                "group_by": "month",
                "start_date": "2025-01-01",
                "end_date": "2025-12-31"
            },
            "expected": lambda d: "list" in d and all(item.get("period") is not None for item in d["list"] if d["list"])
        },
        {
            "name": "에러 코드 필터링",
            "data": {"error_code": "CLN_CHM_200"},
            "expected": lambda d: "list" in d and isinstance(d["list"], list)
        }
    ]
    
    for test_case in test_cases:
        print_test(test_case["name"], test_case["data"])
        try:
            response = await client.post("/api/v1/informnote/stats/error-code", json=test_case["data"], timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                success = test_case["expected"](data)
                count = len(data.get("list", [])) if "list" in data else 0
                test_result(success, f"통계 조회 {'성공' if success else '실패'}: {count}개 결과", {"count": count})
            else:
                test_result(False, f"HTTP {response.status_code} 오류: {response.text[:200]}")
        except Exception as e:
            test_result(False, f"예외 발생: {str(e)}")

async def test_search(client: httpx.AsyncClient):
    """POST /api/v1/informnote/search - 작업내역 검색 테스트"""
    print_header("5. POST /api/v1/informnote/search - 작업내역 검색")
    
    test_cases = [
        {
            "name": "빈 요청",
            "data": {},
            "expected": lambda d: "list" in d and isinstance(d["list"], list)
        },
        {
            "name": "날짜 범위 지정",
            "data": {
                "start_date": "2025-07-01",
                "end_date": "2025-07-31"
            },
            "expected": lambda d: "list" in d and isinstance(d["list"], list)
        },
        {
            "name": "프로세스 필터링",
            "data": {"process_id": "PROC_CLN"},
            "expected": lambda d: "list" in d and isinstance(d["list"], list)
        },
        {
            "name": "상태 필터링 (IN_PROGRESS)",
            "data": {"status_id": 0},
            "expected": lambda d: "list" in d and isinstance(d["list"], list)
        },
        {
            "name": "limit 지정",
            "data": {"limit": 5},
            "expected": lambda d: "list" in d and len(d["list"]) <= 5
        }
    ]
    
    for test_case in test_cases:
        print_test(test_case["name"], test_case["data"])
        try:
            response = await client.post("/api/v1/informnote/search", json=test_case["data"], timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                success = test_case["expected"](data)
                count = len(data.get("list", [])) if "list" in data else 0
                test_result(success, f"검색 {'성공' if success else '실패'}: {count}개 결과", {"count": count})
            else:
                test_result(False, f"HTTP {response.status_code} 오류: {response.text[:200]}")
        except Exception as e:
            test_result(False, f"예외 발생: {str(e)}")

async def test_pm_history(client: httpx.AsyncClient):
    """POST /api/v1/informnote/history/pm - PM 이력 조회 테스트"""
    print_header("6. POST /api/v1/informnote/history/pm - PM 이력 조회")
    
    test_cases = [
        {
            "name": "빈 요청 (기본값)",
            "data": {},
            "expected": lambda d: "list" in d and isinstance(d["list"], list)
        },
        {
            "name": "날짜 범위 지정",
            "data": {
                "start_date": "2025-01-01",
                "end_date": "2025-12-31"
            },
            "expected": lambda d: "list" in d and isinstance(d["list"], list)
        },
        {
            "name": "프로세스 필터링",
            "data": {"process_id": "PROC_CLN"},
            "expected": lambda d: "list" in d and isinstance(d["list"], list)
        },
        {
            "name": "limit 지정",
            "data": {"limit": 5},
            "expected": lambda d: "list" in d and len(d["list"]) <= 5
        }
    ]
    
    for test_case in test_cases:
        print_test(test_case["name"], test_case["data"])
        try:
            response = await client.post("/api/v1/informnote/history/pm", json=test_case["data"], timeout=TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                success = test_case["expected"](data)
                count = len(data.get("list", [])) if "list" in data else 0
                test_result(success, f"PM 이력 조회 {'성공' if success else '실패'}: {count}개 결과", {"count": count})
            else:
                test_result(False, f"HTTP {response.status_code} 오류: {response.text[:200]}")
        except Exception as e:
            test_result(False, f"예외 발생: {str(e)}")

async def test_ask(client: httpx.AsyncClient):
    """POST /ask - 질문-답변 테스트"""
    print_header("7. POST /ask - 질문-답변")
    
    test_cases = [
        {
            "name": "빈 질문",
            "data": {"question": ""},
            "should_fail": True
        },
        {
            "name": "일반 질문",
            "data": {"question": "에러 통계를 알려줘"},
            "should_fail": False
        }
    ]
    
    for test_case in test_cases:
        print_test(test_case["name"], test_case["data"])
        try:
            response = await client.post("/ask", json=test_case["data"], timeout=TIMEOUT)
            
            if test_case.get("should_fail"):
                success = response.status_code != 200
                test_result(success, f"예상대로 실패함 (HTTP {response.status_code})")
            else:
                if response.status_code == 200:
                    data = response.json()
                    required_fields = ["answer", "question", "success"]
                    has_required = all(field in data for field in required_fields)
                    test_result(has_required, f"질문-답변 {'성공' if has_required else '실패'}: success={data.get('success')}", {"success": data.get("success")})
                else:
                    test_result(False, f"HTTP {response.status_code} 오류: {response.text[:200]}")
        except Exception as e:
            test_result(False, f"예외 발생: {str(e)}")

def print_summary():
    """테스트 결과 요약 출력"""
    print_header("테스트 결과 요약")
    
    total = len(test_results)
    passed = sum(1 for r in test_results if r["success"])
    failed = total - passed
    
    print(f"\n총 테스트: {total}개")
    print(f"성공: {passed}개")
    print(f"실패: {failed}개")
    if total > 0:
        print(f"성공률: {(passed/total*100):.1f}%")
    
    if failed > 0:
        print("\n[실패한 테스트]")
        for i, result in enumerate(test_results, 1):
            if not result["success"]:
                print(f"  {i}. {result['message']}")

async def main():
    """메인 실행 함수"""
    print("=" * 70)
    print("  모든 API 엔드포인트 종합 테스트")
    print("=" * 70)
    print(f"\n테스트 대상 서버: {BASE_URL}")
    
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT) as client:
        # 각 API 테스트 실행
        await test_root(client)
        await test_health(client)
        await test_lookup_ids(client)
        await test_error_stats(client)
        await test_search(client)
        await test_pm_history(client)
        await test_ask(client)
    
    # 결과 요약
    print_summary()
    
    # 종료 코드 결정
    failed_count = sum(1 for r in test_results if not r["success"])
    return 0 if failed_count == 0 else 1

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
