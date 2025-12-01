#!/usr/bin/env python3
"""
서버 시작 스크립트 (Windows & macOS/Linux 호환)
더블클릭으로 실행 가능
"""
import sys
import os
import subprocess
import platform
from pathlib import Path

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

def check_venv():
    """가상환경 존재 확인"""
    base_dir = Path(__file__).parent
    venv_dir = base_dir / "venv"
    return venv_dir.exists()

def check_env_file():
    """환경 변수 파일 확인"""
    base_dir = Path(__file__).parent
    env_file = base_dir / ".env"
    return env_file.exists()

def start_server():
    """서버 시작"""
    base_dir = Path(__file__).parent
    system = platform.system()
    
    print("=" * 60)
    print("질문-답변 API 서버 시작")
    print("=" * 60)
    print(f"OS: {system}")
    print(f"작업 디렉토리: {base_dir}")
    print()
    
    # 가상환경 확인
    if not check_venv():
        print("❌ 가상환경을 찾을 수 없습니다.")
        print("먼저 다음 명령어를 실행하세요:")
        print("  - macOS/Linux: ./setup_env.sh")
        print("  - Windows: setup_env.bat (또는 수동 설정)")
        input("\n아무 키나 눌러 종료하세요...")
        return
    
    # 환경 변수 파일 확인
    if not check_env_file():
        print("⚠️  .env 파일을 찾을 수 없습니다.")
        print("서버 시작을 계속합니다...")
        print()
    
    # Python 경로 결정
    python_path = get_venv_python()
    if not python_path:
        print("❌ 가상환경 Python을 찾을 수 없습니다.")
        print("Python 경로를 확인하세요.")
        input("\n아무 키나 눌러 종료하세요...")
        return
    
    print(f"✓ Python 경로: {python_path}")
    print()
    
    # 서버 시작
    main_py = base_dir / "main.py"
    
    print("=" * 60)
    print("서버 시작 중...")
    print("=" * 60)
    print()
    print(f"서버 URL: http://localhost:8000")
    print(f"헬스 체크: http://localhost:8000/health")
    print(f"API 문서: http://localhost:8000/docs")
    print()
    print("서버를 종료하려면 Ctrl+C를 누르세요.")
    print("=" * 60)
    print()
    
    try:
        # 서버 실행
        if system == "Windows":
            # Windows: 콘솔 창이 닫히지 않도록 실행
            subprocess.run([python_path, str(main_py)], cwd=str(base_dir))
        else:
            # macOS/Linux: 직접 실행
            os.execv(python_path, [python_path, str(main_py)])
    except KeyboardInterrupt:
        print("\n\n서버가 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        input("\n아무 키나 눌러 종료하세요...")

if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("\n\n프로그램이 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 치명적 오류: {e}")
        input("\n아무 키나 눌러 종료하세요...")

