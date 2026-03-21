# 指定单件移动到指定文件夹 

from pathlib import Path    # 拿取智能路径工具
import shutil               # 拿取物理搬运工具

def butler_move_task():
    #  1. 确认目标文件
    target_file = Path("test.txt")

    # 2. 确认目标文件夹
    destination = Path("archive")

    # 3. 如果文件夹不存在，先建一个
    # parents=True 表示如果路径很深也一并创建，exist_ok=True 表示已存在不报错
    destination.mkdir(parents=True, exist_ok=True)

    # 4. 检查文件在不在
    if target_file.exists():
        # 计算新家位置：Archive / test.txt
        new_location = destination / target_file.name
        # 执行搬运 (shutil 需要接收字符串格式的路径，所以用 str 转换)
        shutil.move(str(target_file), str(new_location))
        print(f"🤵 管家报告：已将 {target_file.name} 移至 {destination} 文件夹。")
    else:
        print("🤵 管家提示：桌上没找到 test.txt，请您先放一个。")    
# --- 启动开关 (防误触) ---
if __name__ == "__main__":
    print("🔔 正在唤醒您的文件夹管家...")
    butler_move_task()