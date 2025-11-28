# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Uvicorn 관련
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.logging',
        # Oracle DB
        'oracledb',
        # Pydantic 2.x 관련
        'pydantic_settings',
        'pydantic._internal._config',
        'pydantic._internal._generate_schema',
        'pydantic._internal._fields',
        'pydantic._internal._model_construction',
        'pydantic._internal._utils',
        'pydantic._internal._dataclasses',
        'pydantic._internal._decorators',
        'pydantic._internal._validate_call',
        # FastAPI 관련
        'fastapi.middleware.cors',
        'fastapi.responses',
        # HTTP 클라이언트
        'httpx',
        'httpx._client',
        'httpx._transports',
        # 로깅
        'logging',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 불필요한 모듈 제외 (실행 파일 크기 감소)
        'pandas',
        'openpyxl',
        'numpy',
        'matplotlib',
        'tkinter',
        'IPython',
        'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='question-answer-api',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 콘솔 창 표시 (로그 확인용)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 아이콘 파일이 있다면 경로 지정
)

