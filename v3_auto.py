"""
VERSION: v1.0.0 (Build-ready)
STATUS: Stable & Released

FEAT: 完善生产环境配置，支持一键打包 .exe
--------------------------------------------------
- 集成 butler.ico 图标生成脚本
- 优化静态资源路径兼容性（针对 PyInstaller 运行环境）
- 确认为 --noconsole 静默模式后台运行
- 优化文件分类逻辑与自动分拣稳定性，达到正式发布标准
--------------------------------------------------
PACKAGING COMMAND:
pyinstaller --onefile --noconsole --name "智能文件夹管家" --icon=butler.ico --clean v3_auto.py
"""
#from plyer import notification  # 👈 从对讲机库里拿出“通知”零件
from datetime import datetime  # 从时间库里拿出现在的时间工具
import time             # 导入时间工具 (闹钟)
from pathlib import Path    # 拿取智能路径工具
import shutil               # 拿取物理搬运工具
import subprocess  # 👈 用来跟系统对话
import sys
import os


now = datetime.now().strftime("%H:%M:%S") # 👈 这一行是“看表”并把时间变成人类能看懂的格式
print(f"[{now}] 🤵 管家正在穿衣服，准备开工...")
# --- 1. 统计一共移动了多少个文件,在函数外面 ---
total_files_moved = 0


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
        # 关键修改：添加 startupinfo 来隐藏窗口
        # 这在打包成 --noconsole 的 exe 后尤为重要
        import os
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0 # 0 代表隐藏窗口 (SW_HIDE)

        subprocess.run(
            ["powershell", "-Command", powershell_code], 
            capture_output=True, 
            startupinfo=si,  # 👈 传入隐藏参数
            creationflags=subprocess.CREATE_NO_WINDOW # 👈 进一步确保不产生窗口
        )
    except Exception as e:
        print(f"❌ 弹窗尝试失败: {e}")

# --- 核心改进：锁定程序所在的真实目录 ---
# 无论你在哪里运行，这行代码都能找到 .py 或 .exe 所在的那个文件夹
BASE_DIR = Path(sys.argv[0]).resolve().parent
os.chdir(BASE_DIR)  # 强制把工作目录切换到程序所在的地方

def butler_batch_sort():
    global total_files_moved
    # 使用绝对路径，不再使用 "."
    current_dir = BASE_DIR 
    count = 0
    
    # 获取我自己的名字
    my_name = Path(sys.argv[0]).name
    log_name = "butler_log.txt"

    # 打印一下，方便你在调试时看到管家到底在盯着哪个文件夹
    # print(f"正在巡逻: {current_dir}") 

    for item in current_dir.iterdir():
        # 排除逻辑增强
        if (item.is_file() and 
            item.name != my_name and           # 排除自己 (.py 或 .exe)
            item.name != log_name and          # 排除日志
            not item.name.startswith("v3_auto") and # 额外的保险：排除任何以 v3_auto 开头的文件
            item.suffix.lower() != ".exe"):    # 排除所有执行文件
            
            ext = item.suffix.lower().replace(".", "") or "others"
            target_folder = current_dir / ext
            target_folder.mkdir(exist_ok=True)
            
            # 移动文件
            shutil.move(str(item), str(target_folder / item.name))
            count += 1
            total_files_moved += 1



    # ... 弹窗逻辑 ...
    if count > 0:
        log_text = f"🤵 管家报告：刚才自动清理了 {count} 个新文件！累计功劳：{total_files_moved}"
        print(log_text) # 控制台看一眼
        
        # --- 新增：即时写日志 ---
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("butler_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{now}] {log_text}\n")
            # f.flush() # 可选：如果还不放心，可以加这一行强制存盘
        # 调用我们刚写的函数
        send_win_notification(
            "管家整理完毕！", 
            f"刚才处理了 {count} 个文件，累计：{total_files_moved}"
        )
        # 👈 桌面弹窗逻辑
        # notification.notify(
        #     title="管家整理完毕！",
        #     message=f"刚才清理了 {count} 个文件\n累计处理：{total_files_moved} 个",
        #     app_name="文件管家",
        #     timeout=5  # 弹窗停留 5 秒后自动消失
        # )
        #print("DEBUG: 弹窗指令已发出！") # 👈 加这一行

# --- 启动开关 (定时自动化) ---
if __name__ == "__main__":
    print("🚀 自动管家已上线，每 10 秒扫描一次文件夹...")
    print("⚠️  提示：按键盘上的 Ctrl + C 可以解雇管家（停止运行）。")
    
    try:
        while True:
            butler_batch_sort()  # 1. 执行扫除
            time.sleep(10)       # 2. 闭眼休眠 10 秒
    except KeyboardInterrupt:
        # 统一使用带日期的完整时间
        now_full = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构造一行清爽的总结，末尾自带换行
        summary = f"[{now_full}] 👋 管家下班了，本次运行总计搬运：{total_files_moved} 个文件\n"

        with open("butler_log.txt", "a", encoding="utf-8") as f:
            # 直接写入 summary，不要再套一层 [{now}]
            f.write(summary)
            f.flush()
            
        print(f"\n{summary}期待下次为您服务！")