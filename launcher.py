#!/usr/bin/env python3
"""
标准信息检索平台 - 桌面启动器
双击运行 / 打包为独立可执行文件
"""

import os
import socket
import sys
import threading
import time
import webbrowser


def get_base_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def find_app_path(base_dir):
    candidates = [
        os.path.join(base_dir, "app.py"),
        os.path.join(base_dir, "_internal", "app.py"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    for root, _dirs, files in os.walk(base_dir):
        if "app.py" in files:
            return os.path.join(root, "app.py")
    return None


def find_available_port(start=8501, max_tries=20):
    """从 start 开始寻找可用端口。"""
    for port in range(start, start + max_tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start


def open_browser(url, delay=3):
    time.sleep(delay)
    webbrowser.open(url)


def main():
    base_dir = get_base_dir()
    app_path = find_app_path(base_dir)

    if not app_path:
        input(
            "错误：找不到 app.py 文件。\n"
            "请确保 launcher.py 和 app.py 在同一个目录。\n\n按 Enter 退出..."
        )
        sys.exit(1)

    port = find_available_port()
    url = f"http://localhost:{port}"

    print("=" * 52)
    print("      全国标准信息检索平台")
    print("=" * 52)
    print()
    print(f"  正在启动服务...")
    if port != 8501:
        print(f"  端口 8501 已被占用，使用端口 {port}")
    print(f"  启动后浏览器将自动打开")
    print(f"  地址：{url}")
    print()
    print("  关闭窗口或按 Ctrl+C 即可停止")
    print("-" * 52)

    threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    # 直接调用 Streamlit CLI，避免 PyInstaller 下 subprocess 无限重启动
    from streamlit.web import cli as st_cli

    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--server.port",
        str(port),
        "--server.headless",
        "true",
        "--server.enableXsrfProtection",
        "false",
        "--browser.gatherUsageStats",
        "false",
        "--server.fileWatcherType",
        "none",
        "--global.developmentMode",
        "false",
    ]
    try:
        st_cli.main()
    except SystemExit:
        pass
    except Exception as e:
        print(f"\n启动失败: {e}")
        print("请尝试关闭其他程序后重试。")
        input("\n按 Enter 退出...")


if __name__ == "__main__":
    main()
