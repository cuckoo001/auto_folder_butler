# 批量处理把文件整理到对应的文件夹里

from pathlib import Path    # 拿取智能路径工具
import shutil               # 拿取物理搬运工具

def butler_batch_sort():
    # 任务：扫视当前文件夹，按后缀名自动分类所有文件
    #  1. 获取当前所在的路径
    current_dir = Path(".")

    # 开始扫视 (Loop)
    for item in current_dir.iterdir():

        # 3. 筛选：只搬“文件”，不搬“文件夹”，也不搬“自己”
        if item.is_file() and item.name != "v2_batch.py":
            # 4.获取后缀名，去掉点，比如 .txt 变成 txt
            extension = item.suffix.lower().replace(".", "")
            
            # 如果没有后缀名，就归类到 others
            if not extension:
                extension = "others"
            # 5. 创建对应的目录
            target_folder = current_dir / extension
            target_folder.mkdir(exist_ok=True)
            
            # 6. 移动到新目录
            shutil.move(str(item), str(target_folder / item.name))
            print(f"🤵 管家：已将 {item.name} 送往 {extension} 目录。")  
if __name__ == "__main__":
    print("🔔 正在唤醒您的批量整理管家...")
    butler_batch_sort()          
