import sys
print("Start script", flush=True)
try:
    import pandas as pd
    print("Pandas imported successfully", flush=True)
except Exception as e:
    print(f"Error importing pandas: {e}", flush=True)

import oracledb
print("Oracledb imported successfully", flush=True)

