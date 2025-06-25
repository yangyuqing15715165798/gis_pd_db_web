import uvicorn
import os
import sys

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

# 添加当前目录到系统路径
sys.path.append(current_dir)

# 打印一些诊断信息
print(f"当前工作目录: {os.getcwd()}")
print(f"脚本目录: {current_dir}")
print(f"数据库路径: {os.path.join(os.path.dirname(current_dir), 'gis_pd_data.db')}")
print(f"数据库文件是否存在: {os.path.exists(os.path.join(os.path.dirname(current_dir), 'gis_pd_data.db'))}")

if __name__ == "__main__":
    # 启动FastAPI应用
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 