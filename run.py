import sys
import os
from pathlib import Path
import streamlit.web.cli as stcli

if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        base_path = Path(sys.executable).parent
    else:
        base_path = Path(__file__).parent

    os.chdir(base_path)

    # 智能查找 app.py（同时支持直接同级和 _internal 里）
    possible_paths = [
        base_path / "app.py",
        base_path / "_internal" / "app.py",
    ]

    app_path = next((p for p in possible_paths if p.exists()), None)

    if not app_path:
        print("错误：找不到 app.py 文件")
        sys.exit(1)

    sys.argv = [
        "streamlit", "run", str(app_path),
        "--server.headless", "true",
        "--global.developmentMode", "false",
        "--browser.gatherUsageStats", "false",
    ]
    sys.exit(stcli.main())