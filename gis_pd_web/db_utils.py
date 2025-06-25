import sqlite3
import os
import datetime
from typing import List, Dict, Any, Optional

class DatabaseManager:
    """数据库管理类，负责数据库的连接和数据查询"""
    def __init__(self, db_name="gis_pd_data.db"):
        """初始化数据库连接"""
        # 数据库文件路径
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_name)
        self.connected = False
        
        # 测试数据库连接
        try:
            conn = self.get_connection()
            conn.close()
            self.connected = True
            print(f"数据库连接成功: {self.db_path}")
        except sqlite3.Error as e:
            print(f"数据库连接错误: {str(e)}")
    
    def get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 使查询结果可以通过列名访问
        return conn
    
    def get_cycle_data(self, limit=100, offset=0):
        """获取周期数据"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM cycle_data ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            data = cursor.fetchall()
            conn.close()
            
            # 转换为字典列表
            result = []
            for row in data:
                cycle_data = {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "cycle_number": row["cycle_number"],
                    "data": [float(x) for x in row["data"].split(',')]
                }
                result.append(cycle_data)
                
            return result
        except sqlite3.Error as e:
            print(f"获取周期数据错误: {str(e)}")
            return []
    
    def get_latest_cycle_data(self, count=1):
        """获取最新的周期数据"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM cycle_data ORDER BY timestamp DESC LIMIT ?",
                (count,)
            )
            data = cursor.fetchall()
            conn.close()
            
            # 转换为字典列表
            result = []
            for row in data:
                cycle_data = {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "cycle_number": row["cycle_number"],
                    "data": [float(x) for x in row["data"].split(',')]
                }
                result.append(cycle_data)
                
            return result
        except sqlite3.Error as e:
            print(f"获取最新周期数据错误: {str(e)}")
            return []
    
    def get_cycle_data_by_time(self, start_time, end_time):
        """根据时间范围获取周期数据"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM cycle_data WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp",
                (start_time, end_time)
            )
            data = cursor.fetchall()
            conn.close()
            
            # 转换为字典列表
            result = []
            for row in data:
                cycle_data = {
                    "id": row["id"],
                    "timestamp": row["timestamp"],
                    "cycle_number": row["cycle_number"],
                    "data": [float(x) for x in row["data"].split(',')]
                }
                result.append(cycle_data)
                
            return result
        except sqlite3.Error as e:
            print(f"根据时间范围获取周期数据错误: {str(e)}")
            return []
    
    def get_cycle_count(self):
        """获取周期数据总数"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM cycle_data")
            count = cursor.fetchone()["count"]
            conn.close()
            return count
        except sqlite3.Error as e:
            print(f"获取周期数据总数错误: {str(e)}")
            return 0
    
    def get_raw_count(self):
        """获取原始数据总数"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM raw_data")
            count = cursor.fetchone()["count"]
            conn.close()
            return count
        except sqlite3.Error as e:
            print(f"获取原始数据总数错误: {str(e)}")
            return 0
    
    def get_db_stats(self):
        """获取数据库统计信息"""
        try:
            conn = self.get_connection()
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
                "cycle_count": cycle_count,
                "raw_count": raw_count,
                "latest_cycle": latest_cycle,
                "earliest_cycle": earliest_cycle
            }
        except sqlite3.Error as e:
            print(f"获取数据库统计信息错误: {str(e)}")
            return {
                "cycle_count": 0,
                "raw_count": 0,
                "latest_cycle": None,
                "earliest_cycle": None
            } 