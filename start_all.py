#!/usr/bin/env python3
"""
서버 + ngrok 통합 실행 스크립트 (Windows & macOS/Linux 호환)
더블클릭으로 실행 가능
"""
import sys
import os
import subprocess
import platform
import time
import signal
from pathlib import Path
import threading

def get_venv_python():
    """가상환경 Python 경로 반환"""
    base_dir = Path(__file__).parent
    system = platform.system()
    
    if system == "Windows":
        python_path = base_dir / "venv" / "Scripts" / "python.exe"
    else:
        python_path = base_dir / "venv" / "bin" / "python3"
    
    if python_path.exists():
        return str(python_path)
    return None

def find_python_executable():
    """시스템 Python 실행 파일 경로 반환"""
    if platform.system() == "Windows":
        return "python"
    else:
        return "python3"

def check_port(port: int) -> bool:
    """포트가 사용 중인지 확인"""
    system = platform.system()
    try:
        if system == "Windows":
            result = subprocess.run(
                ["netstat", "-ano"], 
                capture_output=True, 
                text=True
            )
            return f":{port}" in result.stdout
        else:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
    except:
        return False

def kill_port_process(port: int):
    """포트를 사용하는 프로세스 종료"""
    system = platform.system()
    try:
        if system == "Windows":
            result = subprocess.run(
                ["netstat", "-ano"], 
                capture_output=True, 
                text=True
            )
            for line in result.stdout.split('\n'):
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        subprocess.run(["taskkill", "/F", "/PID", pid], capture_output=True)
        else:
            subprocess.run(["lsof", "-ti", f":{port}"], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE)
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        subprocess.run(["kill", "-9", pid], capture_output=True)
    except Exception as e:
        print(f"포트 {port} 프로세스 종료 중 오류: {e}")

def wait_for_server(max_wait=30):
    """서버가 시작될 때까지 대기"""
    print("서버 시작 대기 중...", end="", flush=True)
    for i in range(max_wait):
        try:
            import urllib.request
            response = urllib.request.urlopen("http://localhost:8000/health", timeout=2)
            if response.getcode() == 200:
                print(" ✅")
                return True
        except:
            pass
        print(".", end="", flush=True)
        time.sleep(1)
    print(" ❌ (타임아웃)")
    return False

def run_server(python_executable: str, base_dir: Path):
    """서버 실행"""
    print("\n" + "=" * 60)
    print("1. API 서버 시작 중...")
    print("=" * 60)
    
    # 기존 서버 프로세스 종료
    if check_port(8000):
        print("기존 서버 프로세스 종료 중...")
        kill_port_process(8000)
        time.sleep(2)
    
    server_command = [
        python_executable,
        "-c",
        "import uvicorn; uvicorn.run('main:app', host='0.0.0.0', port=8000, log_level='info')"
    ]
    
    if platform.system() == "Windows":
        process = subprocess.Popen(
            server_command,
            cwd=str(base_dir),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        process = subprocess.Popen(
            server_command,
            cwd=str(base_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            start_new_session=True
        )
    
    return process

def run_ngrok(python_executable: str, base_dir: Path):
    """ngrok 실행"""
    print("\n" + "=" * 60)
    print("2. ngrok 터널 시작 중...")
    print("=" * 60)
    
    # 기존 ngrok 프로세스 종료
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], 
                         capture_output=True)
        else:
            subprocess.run(["pkill", "-f", "ngrok http 8000"], 
                         capture_output=True)
        time.sleep(2)
    except:
        pass
    
    # 서버가 시작될 때까지 대기
    if not wait_for_server():
        print("❌ 서버가 시작되지 않아 ngrok을 시작할 수 없습니다.")
        return None
    
    # ngrok 경로 찾기
    ngrok_path = None
    if system == "Windows":
        # Windows: PATH에서 찾기
        ngrok_path = "ngrok"
    else:
        # macOS/Linux: 일반적인 경로 확인
        possible_paths = [
            Path.home() / "bin" / "ngrok",
            Path("/usr/local/bin/ngrok"),
            Path("/usr/bin/ngrok"),
        ]
        for path in possible_paths:
            if path.exists():
                ngrok_path = str(path)
                break
        if not ngrok_path:
            ngrok_path = "ngrok"
    
    print(f"ngrok 경로: {ngrok_path}")
    
    ngrok_command = [ngrok_path, "http", "8000", "--log=stdout"]
    
    if system == "Windows":
        process = subprocess.Popen(
            ngrok_command,
            cwd=str(base_dir),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        # macOS/Linux: ngrok PATH 추가
        env = os.environ.copy()
        env["PATH"] = f"{Path.home() / 'bin'}:{env.get('PATH', '')}"
        process = subprocess.Popen(
            ngrok_command,
            cwd=str(base_dir),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            start_new_session=True
        )
    
    # ngrok URL 출력 (약간 대기 후)
    time.sleep(3)
    print("\nngrok 터널이 시작되었습니다.")
    print("ngrok 웹 UI에서 URL을 확인하세요: http://127.0.0.1:4040")
    
    return process

def main():
    base_dir = Path(__file__).parent
    os.chdir(base_dir)
    
    print("=" * 60)
    print("API 서버 + ngrok 통합 실행 스크립트")
    print("=" * 60)
    
    # 1. 가상환경 Python 찾기
    python_executable = get_venv_python()
    if not python_executable:
        print("⚠ 경고: 가상환경 Python을 찾을 수 없습니다. 시스템 Python을 사용합니다.")
        python_executable = find_python_executable()
    print(f"✅ 사용할 Python: {python_executable}")
    
    # 2. .env 파일 확인
    env_file = base_dir / ".env"
    if not env_file.exists():
        print("❌ 오류: .env 파일이 프로젝트 루트에 없습니다.")
        print("     Oracle DB 연결 정보가 포함된 .env 파일을 생성해주세요.")
        print("     자세한 내용은 README.md를 참조하세요.")
        sys.exit(1)
    print(f"✅ .env 파일 확인: {env_file}")
    
    processes = []
    
    try:
        # 3. 서버 실행
        server_process = run_server(python_executable, base_dir)
        processes.append(("서버", server_process))
        
        # 4. ngrok 실행
        ngrok_process = run_ngrok(python_executable, base_dir)
        if ngrok_process:
            processes.append(("ngrok", ngrok_process))
        
        print("\n" + "=" * 60)
        print("✅ 모든 서비스가 시작되었습니다!")
        print("=" * 60)
        print("\n서버 URL: http://localhost:8000")
        print("ngrok 웹 UI: http://127.0.0.1:4040")
        print("\n종료하려면 Ctrl+C를 누르세요...")
        print("=" * 60)
        
        # 프로세스 출력 모니터링
        def monitor_process(name, process):
            if process:
                for line in process.stdout:
                    print(f"[{name}] {line}", end='')
        
        threads = []
        for name, proc in processes:
            if proc:
                thread = threading.Thread(
                    target=monitor_process, 
                    args=(name, proc),
                    daemon=True
                )
                thread.start()
                threads.append(thread)
        
        # 대기
        try:
            while True:
                time.sleep(1)
                # 프로세스가 종료되었는지 확인
                for name, proc in processes:
                    if proc and proc.poll() is not None:
                        print(f"\n⚠ {name} 프로세스가 종료되었습니다 (종료 코드: {proc.returncode})")
        except KeyboardInterrupt:
            print("\n\n종료 신호 수신...")
        
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
    
    finally:
        # 모든 프로세스 종료
        print("\n모든 프로세스 종료 중...")
        for name, proc in processes:
            if proc:
                try:
                    proc.terminate()
                    proc.wait(timeout=5)
                except:
                    proc.kill()
                print(f"✅ {name} 종료됨")
        
        print("\n" + "=" * 60)
        print("모든 서비스가 종료되었습니다.")
        print("=" * 60)

if __name__ == "__main__":
    main()

