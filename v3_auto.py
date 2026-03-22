# 自动定时 增加桌面弹窗提醒功能
from plyer import notification  # 👈 从对讲机库里拿出“通知”零件
from datetime import datetime  # 从时间库里拿出现在的时间工具
import time             # 导入时间工具 (闹钟)
from pathlib import Path    # 拿取智能路径工具
import shutil               # 拿取物理搬运工具

now = datetime.now().strftime("%H:%M:%S") # 👈 这一行是“看表”并把时间变成人类能看懂的格式
print(f"[{now}] 🤵 管家正在穿衣服，准备开工...")
# --- 1. 统计一共移动了多少个文件,在函数外面 ---
total_files_moved = 0
def butler_batch_sort():
    """这是刚才写好的批量处理逻辑"""
    # 声明我们要用外面那个total_files_moved变量
    global total_files_moved
    current_dir = Path(".")
    count = 0   # 这是“这一轮”的小计，每次进函数都会清零
    for item in current_dir.iterdir():
        # 排除文件夹和脚本自己和生成的日志文件
        if item.is_file() and item.name != "v3_auto.py" and item.name != "butler_log.txt":
            ext = item.suffix.lower().replace(".", "") or "others"
            target_folder = current_dir / ext
            target_folder.mkdir(exist_ok=True)
            shutil.move(str(item), str(target_folder / item.name))
            count += 1  # 本轮加 1
            total_files_moved += 1  # 总数加 1 
    
    if count > 0:
        print(f"🤵 管家报告：刚才自动清理了 {count} 个新文件！")
        print(f"🏆 累计功劳：已经帮您处理了 {total_files_moved} 个文件！")

        # 👈 桌面弹窗逻辑
        notification.notify(
            title="管家整理完毕！",
            message=f"刚才清理了 {count} 个文件\n累计处理：{total_files_moved} 个",
            app_name="文件管家",
            timeout=5  # 弹窗停留 5 秒后自动消失
        )
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
        now = datetime.now().strftime("%H:%M:%S")
        # 👈 把 \n 挪到最后，这样每条记录后面都会自动准备好下一行
        summary = f"[{now}] 👋 管家下班了，总计搬运：{total_files_moved} 个文件\n"

        with open("butler_log.txt", "a", encoding="utf-8") as f:
            f.write(summary)
            
        # 这里的 print 可以保留 \n 让控制台好看一点
        print(f"\n{summary}期待下次为您服务！")