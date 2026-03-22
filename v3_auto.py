"""
VERSION: v3.0.1 (终极稳定版 - 超详细注释)
作用：文件夹智能整理管家
特点：
1. 监控当前文件夹，自动按后缀分类文件。
2. 托盘图标显示，不占用任务栏。
3. 实时更新处理数量，解决菜单不刷新的 Bug。
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

# ==========================================
# 1. 路径锁定：解决“管家住哪儿”的问题
# ==========================================
# 当你把程序打包成 .exe 后，它的运行环境会变。
# 这段代码确保管家永远盯着 .exe 所在的那个文件夹，而不是系统临时目录。
if getattr(sys, 'frozen', False):
    # 打包后的 exe 环境
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    # 直接运行 .py 脚本的环境
    BASE_DIR = Path(__file__).resolve().parent

# 将程序的工作重心切换到这个目录
os.chdir(BASE_DIR)
LOG_NAME = "butler_log.txt"

# ==========================================
# 2. 共享账本：解决“信息同步”的问题
# ==========================================
# STATE 是一个字典，在 Python 里它是“共享地址”的。
# 监控线程在里面加 1，托盘线程点开菜单看一眼，数据是同步的。
STATE = {"total": 0}

# main_icon 用来存放托盘图标对象。
# 把它设为全局，是为了让后台干活的管家能随时“拍一下”前台经理的肩膀要求刷新。
main_icon = None  

# ==========================================
# 3. 消息通知：调用系统气泡
# ==========================================
def send_win_notification(title, message):
    """利用 Windows 自带的 PowerShell 发送右下角弹窗通知"""
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
        # 启动参数：不显示 PowerShell 黑色窗口，静默执行
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        subprocess.run(["powershell", "-Command", powershell_code], 
                       capture_output=True, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
    except:
        pass

# ==========================================
# 4. 核心分拣逻辑：辛勤工作的工人
# ==========================================
def butler_core_logic():
    global main_icon
    while True:
        try:
            count = 0
            my_name = Path(sys.argv[0]).name # 获取程序自己的名字，避免把自己给搬走了
            
            # 扫描 BASE_DIR 下的所有文件
            for item_path in BASE_DIR.iterdir():
                if item_path.is_file():
                    name_lower = item_path.name.lower()
                    
                    # 排除逻辑：如果是程序自己、日志文件、图标、或者其他的 exe，就不动它们
                    # --- 改进后的排除逻辑 ---
                    # 1. 获取当前运行脚本的文件名
                    current_script = Path(sys.argv[0]).name.lower()
                    
                    # 2. 增加硬编码排除（防止它搬走源代码）
                    if (name_lower == current_script or 
                        name_lower == "v3_auto.py" or  # 👈 显式排除源码
                        name_lower == LOG_NAME.lower() or 
                        name_lower == "butler.ico" or 
                        name_lower == "butler.png" or 
                        item_path.suffix.lower() == ".exe"):
                        continue
                    
                    # 获取后缀（比如 .jpg -> jpg），如果没有后缀就丢进 others 文件夹
                    ext = item_path.suffix.lower().replace(".", "") or "others"
                    target_folder = BASE_DIR / ext
                    
                    # 自动创建对应后缀的文件夹
                    target_folder.mkdir(exist_ok=True)
                    
                    # 执行搬运操作
                    shutil.move(str(item_path), str(target_folder / item_path.name))
                    
                    count += 1
                    STATE["total"] += 1 # 在公共账本上记一笔

            # 如果这一轮巡逻发现了文件并进行了搬运
            if count > 0:
                log_msg = f"清理了 {count} 个文件，当前累计: {STATE['total']}"
                # 记录到日志文件
                with open(LOG_NAME, "a", encoding="utf-8") as f:
                    f.write(f"[{datetime.now().strftime('%H:%M:%S')}] 🤵 {log_msg}\n")
                
                # ⭐【核心修复】主动出击！
                # 告诉托盘图标：我的菜单内容变了，请立刻丢弃旧缓存，重新读取 STATE 里的数据。
                if main_icon:
                    main_icon.update_menu()
                
                # 发送 Windows 弹窗
                send_win_notification("管家整理完毕", log_msg)
                
        except Exception as e:
            # 如果出错，记录错误原因
            with open(LOG_NAME, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] ❌ 报错: {str(e)}\n")
        
        # 每隔 5 秒巡逻一次，既保证效率又不会过度占用 CPU
        time.sleep(5)

# ==========================================
# 5. 托盘图标：展示界面
# ==========================================
def on_quit(icon, item):
    """点击“强制下班”时的退出逻辑"""
    icon.stop() # 停止托盘图标
    os._exit(0) # 彻底强制结束整个程序进程

def get_status_text(item):
    """菜单的第一行文字，每次右键点击时都会通过这个函数动态生成"""
    return f"累计处理: {STATE['total']} 个文件"

def setup_tray():
    global main_icon
    # 尝试加载图标图片
    icon_path = BASE_DIR / "butler.png"
    try:
        image = Image.open(icon_path)
    except:
        # 如果找不到图，就画一个蓝色的方块作为图标
        image = Image.new('RGB', (64, 64), color=(0, 120, 215))

    # 定义右键点击菜单的内容
    menu = (
        # 第一个 item 传入的是函数名 get_status_text，确保文字是动态的
        item(get_status_text, lambda: None, enabled=True),
        item('打开日志', lambda icon, item: os.startfile(LOG_NAME)),
        item('强制下班 (退出)', on_quit),
    )
    
    # 初始化托盘图标
    main_icon = pystray.Icon("butler", image, "智能文件夹管家", menu)
    
    # ⭐ 开启双线作战：
    # 创建一个后台线程专门跑 butler_core_logic（搬运工）。
    # daemon=True 意味着主程序（托盘图标）一旦关掉，后台搬运工也立刻跟着停，不会变死循环。
    thread = threading.Thread(target=butler_core_logic, daemon=True)
    thread.start()
    
    # 启动托盘图标，程序会一直运行到你点退出为止
    main_icon.run()

# 程序入口
if __name__ == "__main__":
    setup_tray()