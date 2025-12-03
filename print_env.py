import sys
from pathlib import Path

LOG_FILE = Path("env_log.txt")

try:
    # 시스템 경로에 현재 디렉토리 추가
    sys.path.append(str(Path(__file__).parent))
    
    from config import settings
    
    with open(LOG_FILE, "w") as f:
        f.write(f"USER={settings.ORACLE_USER}\n")
        f.write(f"PASSWORD={settings.ORACLE_PASSWORD}\n")
        f.write(f"DSN={settings.ORACLE_DSN}\n")
        
except Exception as e:
    with open(LOG_FILE, "w") as f:
        f.write(f"ERROR: {e}")


