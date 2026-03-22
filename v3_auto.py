"""
VERSION: v3.0.1(Force Refresh Edition)
STATUS: Last Stand

FEAT: 增加 icon.update_menu() 强制重绘逻辑，彻底粉碎菜单不更新的 Bug
--------------------------------------------------
- 核心改动：在后台线程搬运成功后，主动触发托盘图标的菜单刷新接口
- 优化：将 icon 对象设为全局，确保监控线程可以“越权”操作图标
--------------------------------------------------
"""

import os
import sys
import time
import shutil
import threading
import subprocess
import pystray
from datetime import datetime
from pathlib import Path
from PIL import Image
from pystray import MenuItem as item

# --- 1. 路径锁定 ---
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

os.chdir(BASE_DIR)
LOG_NAME = "butler_log.txt"

# 全局状态字典
STATE = {"total": 0}
main_icon = None  # 👈 新增：用来存放托盘对象，方便跨线程刷新

# --- 2. 通知函数 ---
def send_win_notification(title, message):
    powershell_code = f"""
    [void] [System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms');
    $objNotifyIcon = New-Object System.Windows.Forms.NotifyIcon;
    $objNotifyIcon.Icon = [System.Drawing.SystemIcons]::Information;
    $objNotifyIcon.BalloonTipIcon = 'Info';
    $objNotifyIcon.BalloonTipText = '{message}';
    $objNotifyIcon.BalloonTipTitle = '{title}';
    $objNotifyIcon.Visible = $True;
    $objNotifyIcon.ShowBalloonTip(5000);
    """
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        subprocess.run(["powershell", "-Command", powershell_code], capture_output=True, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    except:
        pass

# --- 3. 监控逻辑 ---
def butler_core_logic():
    global main_icon
    while True:
        try:
            count = 0
            my_name = Path(sys.argv[0]).name
            for item_path in BASE_DIR.iterdir():
                if item_path.is_file():
                    name_lower = item_path.name.lower()
                    if (name_lower == my_name.lower() or name_lower == LOG_NAME.lower() or 
                        name_lower == "butler.ico" or name_lower == "butler.png" or 
                        item_path.suffix.lower() == ".exe"):
                        continue
                    
                    ext = item_path.suffix.lower().replace(".", "") or "others"
                    target_folder = BASE_DIR / ext
                    target_folder.mkdir(exist_ok=True)
                    shutil.move(str(item_path), str(target_folder / item_path.name))
                    
                    count += 1
                    STATE["total"] += 1

            if count > 0:
                log_msg = f"清理了 {count} 个文件，当前累计: {STATE['total']}"
                with open(LOG_NAME, "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now().strftime('%H:%M:%S')}] 🤵 {log_msg}\n")
                
                # ⭐【核心修复】如果图标已经存在，强制它刷新菜单文字
                if main_icon:
                    main_icon.update_menu()
                
                send_win_notification("管家整理完毕", log_msg)
        except Exception as e:
            with open(LOG_NAME, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] ❌ 错误: {str(e)}\n")
        time.sleep(5)

# --- 4. 托盘控制 ---
def on_quit(icon, item):
    icon.stop()
    os._exit(0)

def get_status_text(item):
    return f"累计处理: {STATE['total']} 个文件"

def setup_tray():
    global main_icon
    icon_path = BASE_DIR / "butler.png"
    try:
        image = Image.open(icon_path)
    except:
        image = Image.new('RGB', (64, 64), color=(0, 120, 215))

    # 创建菜单
    menu = (
        item(get_status_text, lambda: None, enabled=True),
        item('打开日志', lambda icon, item: os.startfile(LOG_NAME)),
        item('强制下班 (退出)', on_quit),
    )
    
    main_icon = pystray.Icon("butler", image, "智能文件夹管家", menu)
    
    # 启动后台线程
    thread = threading.Thread(target=butler_core_logic, daemon=True)
    thread.start()
    
    main_icon.run()

if __name__ == "__main__":
    setup_tray()