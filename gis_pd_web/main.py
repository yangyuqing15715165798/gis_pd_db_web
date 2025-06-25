from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import json
import asyncio
import os
import datetime
from typing import List, Dict, Any, Optional
import numpy as np
from pydantic import BaseModel

# 创建FastAPI应用
app = FastAPI(title="GIS局部放电在线监测系统")

# 挂载静态文件
app.mount("/static", StaticFiles(directory="gis_pd_web/static"), name="static")

# 设置模板
templates = Jinja2Templates(directory="gis_pd_web/templates")

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "gis_pd_data.db")

# WebSocket连接管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# 数据库连接
def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# 首页路由
@app.get("/", response_class=HTMLResponse)
async def get_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# 获取最新周期数据
@app.get("/api/latest_cycle_data")
async def get_latest_cycle_data(count: int = 10):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM cycle_data ORDER BY timestamp DESC LIMIT ?",
            (count,)
        )
        data = cursor.fetchall()
        conn.close()
        
        # 转换数据格式，并按时间戳升序排列（从旧到新）
        result = []
        for row in data:
            cycle_data = {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "cycle_number": row["cycle_number"],
                "data": [float(x) for x in row["data"].split(',')]
            }
            result.append(cycle_data)
        
        # 按时间戳升序排列，确保数据按时间顺序
        result.sort(key=lambda x: x["timestamp"])
        
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 获取时间范围内的周期数据
@app.get("/api/cycle_data_by_time")
async def get_cycle_data_by_time(start_time: str, end_time: str):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM cycle_data WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp",
            (start_time, end_time)
        )
        data = cursor.fetchall()
        conn.close()
        
        result = []
        for row in data:
            cycle_data = {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "cycle_number": row["cycle_number"],
                "data": [float(x) for x in row["data"].split(',')]
            }
            result.append(cycle_data)
        
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

# 获取数据库统计信息
@app.get("/api/db_stats")
async def get_db_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取周期数据总数
        cursor.execute("SELECT COUNT(*) as count FROM cycle_data")
        cycle_count = cursor.fetchone()["count"]
        
        # 获取原始数据总数
        cursor.execute("SELECT COUNT(*) as count FROM raw_data")
        raw_count = cursor.fetchone()["count"]
        
        # 获取最新周期数据的时间戳
        cursor.execute("SELECT MAX(timestamp) as latest FROM cycle_data")
        latest_cycle = cursor.fetchone()["latest"]
        
        # 获取最早周期数据的时间戳
        cursor.execute("SELECT MIN(timestamp) as earliest FROM cycle_data")
        earliest_cycle = cursor.fetchone()["earliest"]
        
        conn.close()
        
        return {
            "success": True,
            "data": {
                "cycle_count": cycle_count,
                "raw_count": raw_count,
                "latest_cycle": latest_cycle,
                "earliest_cycle": earliest_cycle
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# 跟踪最新数据ID
last_data_id = 0

# 检查数据库是否有新数据
async def check_new_data():
    global last_data_id
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取最新数据的ID
        cursor.execute("SELECT MAX(id) as max_id FROM cycle_data")
        result = cursor.fetchone()
        max_id = result["max_id"] if result and result["max_id"] is not None else 0
        
        # 如果有新数据
        if max_id > last_data_id:
            # 获取新数据，增加获取数量以确保PRPS图表有足够数据
            cursor.execute(
                "SELECT * FROM cycle_data WHERE id > ? ORDER BY timestamp DESC LIMIT 50",
                (last_data_id,)
            )
            data = cursor.fetchall()
            
            # 更新最新数据ID
            last_data_id = max_id
            
            # 转换数据格式
            result = []
            for row in data:
                cycle_data = {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "cycle_number": row["cycle_number"],
                    "data": [float(x) for x in row["data"].split(',')]
                }
                result.append(cycle_data)
            
            # 按时间戳升序排列，确保数据按时间顺序
            result.sort(key=lambda x: x["timestamp"])
            
            return {"success": True, "data": result, "has_new_data": True}
        
        conn.close()
        return {"success": True, "data": [], "has_new_data": False}
    except Exception as e:
        print(f"检查新数据错误: {str(e)}")
        return {"success": False, "error": str(e), "has_new_data": False}

# WebSocket路由，用于实时数据推送
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # 发送初始数据，获取50个周期以满足PRPS图表需求
        latest_data = await get_latest_cycle_data(count=50)
        await websocket.send_json(latest_data)
        
        # 获取当前最新数据ID
        global last_data_id
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(id) as max_id FROM cycle_data")
        result = cursor.fetchone()
        last_data_id = result["max_id"] if result and result["max_id"] is not None else 0
        conn.close()
        
        # 实时检查数据库更新
        while True:
            # 每隔1秒检查一次数据库更新
            await asyncio.sleep(1)
            new_data = await check_new_data()
            
            # 只有在有新数据时才发送
            if new_data["has_new_data"]:
                await websocket.send_json(new_data)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# 启动服务器时的事件
@app.on_event("startup")
async def startup_event():
    print(f"服务器启动，数据库路径: {os.path.abspath(DB_PATH)}")
    # 检查数据库连接
    try:
        conn = get_db_connection()
        conn.close()
        print("数据库连接成功")
    except Exception as e:
        print(f"数据库连接失败: {str(e)}")

# 关闭服务器时的事件
@app.on_event("shutdown")
async def shutdown_event():
    print("服务器关闭")

# 数据库测试和诊断路由
@app.get("/api/db_test")
async def test_database():
    try:
        # 检查数据库文件是否存在
        if not os.path.exists(DB_PATH):
            return {
                "success": False,
                "error": f"数据库文件不存在: {DB_PATH}",
                "absolute_path": os.path.abspath(DB_PATH)
            }
        
        # 尝试连接数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='cycle_data' OR name='raw_data')")
        tables = cursor.fetchall()
        table_names = [table["name"] for table in tables]
        
        # 获取数据统计
        cycle_count = 0
        raw_count = 0
        latest_cycle = None
        
        if "cycle_data" in table_names:
            cursor.execute("SELECT COUNT(*) as count FROM cycle_data")
            cycle_count = cursor.fetchone()["count"]
            
            if cycle_count > 0:
                cursor.execute("SELECT * FROM cycle_data ORDER BY id DESC LIMIT 1")
                latest_record = cursor.fetchone()
                if latest_record:
                    latest_cycle = {
                        "id": latest_record["id"],
                        "timestamp": latest_record["timestamp"],
                        "cycle_number": latest_record["cycle_number"],
                        "data_length": len(latest_record["data"].split(',')) if latest_record["data"] else 0
                    }
        
        if "raw_data" in table_names:
            cursor.execute("SELECT COUNT(*) as count FROM raw_data")
            raw_count = cursor.fetchone()["count"]
        
        conn.close()
        
        return {
            "success": True,
            "database_path": DB_PATH,
            "absolute_path": os.path.abspath(DB_PATH),
            "tables": table_names,
            "cycle_data_count": cycle_count,
            "raw_data_count": raw_count,
            "latest_cycle": latest_cycle
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "database_path": DB_PATH,
            "absolute_path": os.path.abspath(DB_PATH)
        }

# 如果直接运行此文件
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 