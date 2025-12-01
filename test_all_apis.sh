#!/bin/bash

BASE_URL="http://localhost:8000"
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

print_header() {
    echo ""
    echo "======================================================================"
    echo "  $1"
    echo "======================================================================"
}

print_test() {
    echo ""
    echo "[테스트] $1"
    if [ -n "$2" ]; then
        echo "  요청: $2"
    fi
}

test_result() {
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    if [ "$1" = "success" ]; then
        echo "  ✓ 성공: $2"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo "  ✗ 실패: $2"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
    if [ -n "$3" ]; then
        echo "  응답: $3"
    fi
}

# 1. GET / - 루트 엔드포인트
print_header "1. GET / - 루트 엔드포인트"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    if echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if 'message' in data and 'version' in data else 1)" 2>/dev/null; then
        test_result "success" "루트 엔드포인트 정상 응답" "$(echo "$BODY" | head -c 100)"
    else
        test_result "fail" "응답 형식이 올바르지 않음"
    fi
else
    test_result "fail" "HTTP $HTTP_CODE 오류"
fi

# 2. GET /health - 헬스체크
print_header "2. GET /health - 헬스체크"
RESPONSE=$(curl -s -w "\n%{http_code}" "$BASE_URL/health")
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    if echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); exit(0 if 'status' in data and 'database_connected' in data and 'dify_enabled' in data else 1)" 2>/dev/null; then
        DB_STATUS=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['database_connected'])" 2>/dev/null)
        test_result "success" "헬스체크 정상 (DB: $DB_STATUS)"
    else
        test_result "fail" "필수 필드 누락"
    fi
else
    test_result "fail" "HTTP $HTTP_CODE 오류"
fi

# 3. POST /lookup/ids - ID 조회
print_header "3. POST /lookup/ids - ID 조회"

# 테스트 케이스 1: process_name만 입력
print_test "process_name만 입력 (Cleaning)" '{"process_name": "Cleaning"}'
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/lookup/ids" \
    -H "Content-Type: application/json" \
    -d '{"process_name": "Cleaning"}')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    PROCESS_ID=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('process_id', 'null'))" 2>/dev/null)
    if [ "$PROCESS_ID" != "null" ] && [ -n "$PROCESS_ID" ]; then
        test_result "success" "process_id 반환: $PROCESS_ID"
    else
        test_result "fail" "process_id가 null이거나 없음"
    fi
else
    test_result "fail" "HTTP $HTTP_CODE 오류"
fi

# 테스트 케이스 2: 존재하지 않는 값
print_test "존재하지 않는 값" '{"process_name": "NonExistentProcess"}'
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/lookup/ids" \
    -H "Content-Type: application/json" \
    -d '{"process_name": "NonExistentProcess"}')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    PROCESS_ID=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('process_id', 'null'))" 2>/dev/null)
    if [ "$PROCESS_ID" = "null" ] || [ -z "$PROCESS_ID" ]; then
        test_result "success" "존재하지 않는 값에 대해 null 반환"
    else
        test_result "fail" "존재하지 않는 값인데 결과가 반환됨: $PROCESS_ID"
    fi
else
    test_result "fail" "HTTP $HTTP_CODE 오류"
fi

# 4. POST /api/v1/informnote/stats/error-code - 에러 통계 조회
print_header "4. POST /api/v1/informnote/stats/error-code - 에러 통계 조회"

# 테스트 케이스 1: 빈 요청
print_test "빈 요청 (전체 통계)" '{}'
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/informnote/stats/error-code" \
    -H "Content-Type: application/json" \
    -d '{}')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    COUNT=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('list', [])))" 2>/dev/null)
    if [ -n "$COUNT" ] && [ "$COUNT" -ge 0 ]; then
        test_result "success" "통계 조회 성공: $COUNT개 결과"
    else
        test_result "fail" "응답 형식 오류"
    fi
else
    test_result "fail" "HTTP $HTTP_CODE 오류"
fi

# 테스트 케이스 2: 프로세스 필터링
print_test "프로세스 필터링" '{"process_id": "PROC_CLN"}'
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/informnote/stats/error-code" \
    -H "Content-Type: application/json" \
    -d '{"process_id": "PROC_CLN"}')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    COUNT=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('list', [])))" 2>/dev/null)
    if [ -n "$COUNT" ] && [ "$COUNT" -ge 0 ]; then
        test_result "success" "프로세스 필터링 성공: $COUNT개 결과"
    else
        test_result "fail" "응답 형식 오류"
    fi
else
    test_result "fail" "HTTP $HTTP_CODE 오류"
fi

# 5. POST /api/v1/informnote/search - 작업내역 검색
print_header "5. POST /api/v1/informnote/search - 작업내역 검색"

# 테스트 케이스 1: 빈 요청
print_test "빈 요청" '{}'
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/informnote/search" \
    -H "Content-Type: application/json" \
    -d '{}')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    COUNT=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('list', [])))" 2>/dev/null)
    if [ -n "$COUNT" ] && [ "$COUNT" -ge 0 ]; then
        test_result "success" "검색 성공: $COUNT개 결과"
    else
        test_result "fail" "응답 형식 오류"
    fi
else
    test_result "fail" "HTTP $HTTP_CODE 오류"
fi

# 6. POST /api/v1/informnote/history/pm - PM 이력 조회
print_header "6. POST /api/v1/informnote/history/pm - PM 이력 조회"

# 테스트 케이스 1: 빈 요청
print_test "빈 요청 (기본값)" '{}'
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/v1/informnote/history/pm" \
    -H "Content-Type: application/json" \
    -d '{}')
HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" = "200" ]; then
    COUNT=$(echo "$BODY" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('list', [])))" 2>/dev/null)
    if [ -n "$COUNT" ] && [ "$COUNT" -ge 0 ]; then
        test_result "success" "PM 이력 조회 성공: $COUNT개 결과"
    else
        test_result "fail" "응답 형식 오류"
    fi
else
    test_result "fail" "HTTP $HTTP_CODE 오류"
fi

# 결과 요약
print_header "테스트 결과 요약"

echo ""
echo "총 테스트: $TOTAL_TESTS개"
echo "성공: $PASSED_TESTS개"
echo "실패: $FAILED_TESTS개"
if [ "$TOTAL_TESTS" -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=1; $PASSED_TESTS * 100 / $TOTAL_TESTS" | bc)
    echo "성공률: ${SUCCESS_RATE}%"
fi
echo ""

exit $FAILED_TESTS

