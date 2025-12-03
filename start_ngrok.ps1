# ngrok 자동 실행 스크립트 (Windows PowerShell)
# 기능: ngrok을 백그라운드로 실행하고 Public URL을 출력합니다.
# 이미 실행 중이라면 실행 중인 URL을 찾아줍니다.

$ngrok_port = 8000
$log_file = "$env:TEMP\ngrok.log"

# 1. ngrok 프로세스 확인
$running = Get-Process ngrok -ErrorAction SilentlyContinue

if ($running) {
    Write-Host "✅ ngrok is already running." -ForegroundColor Green
} else {
    Write-Host "🚀 Starting ngrok on port $ngrok_port..." -ForegroundColor Cyan
    # ngrok 백그라운드 실행 (로그 파일 저장 - Output과 Error 분리)
    Start-Process -FilePath "ngrok" -ArgumentList "http $ngrok_port --log=stdout" -RedirectStandardOutput "$log_file" -WindowStyle Hidden
    
    # 실행 대기
    Start-Sleep -Seconds 3
}

# 2. URL 추출 (API 호출 또는 로그 파일 파싱)
# ngrok 로컬 API를 통해 URL 확인이 가장 정확함
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -ErrorAction Stop
    $url = $response.tunnels[0].public_url
    
    if ($url) {
        Write-Host "`n========================================================" -ForegroundColor Yellow
        Write-Host "🔗 ngrok Public URL: $url" -ForegroundColor White
        Write-Host "========================================================" -ForegroundColor Yellow
        Write-Host "👉 Dify/Postman에서 이 URL을 사용하세요."
    } else {
        Write-Host "⚠️ ngrok is running but no tunnel found." -ForegroundColor Red
    }
} catch {
    Write-Host "⚠️ Failed to get ngrok URL. Check $log_file" -ForegroundColor Red
    Write-Host "Tip: Make sure ngrok is installed and in your PATH."
}

