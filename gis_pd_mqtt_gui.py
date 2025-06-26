import sys
import numpy as np
import paho.mqtt.client as mqtt
import matplotlib
# 在导入Figure前设置matplotlib使用PySide6后端
matplotlib.use('QtAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                              QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                              QGroupBox, QGridLayout, QSpinBox, QComboBox, 
                              QStatusBar, QMessageBox, QCheckBox, QDoubleSpinBox,
                              QTableWidget, QTableWidgetItem, QDialog, QDateTimeEdit,
                              QScrollArea, QFileDialog)
from PySide6.QtCore import Qt, QTimer, Signal, Slot, QThread, QMutex, QDateTime
from matplotlib import rcParams
from mpl_toolkits.mplot3d import Axes3D
import time
import queue
import sqlite3
import os
import datetime
import csv  # 导入csv模块用于保存CSV文件

# 设置matplotlib中文支持
rcParams['font.sans-serif'] = ['SimHei']  # 设置中文字体支持
rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 优化matplotlib性能
matplotlib.rcParams['path.simplify'] = True
matplotlib.rcParams['path.simplify_threshold'] = 1.0
matplotlib.rcParams['agg.path.chunksize'] = 10000

class DatabaseManager:
    """数据库管理类，负责数据库的连接、创建表和数据存储"""
    def __init__(self, db_name="gis_pd_data.db"):
        """初始化数据库连接"""
        # 数据库文件路径
        try:
            # 获取应用程序根目录
            if getattr(sys, 'frozen', False):
                # 如果是打包后的应用程序，使用可执行文件所在目录
                # 注意：不使用sys._MEIPASS，因为那是临时目录，应用关闭后会被删除
                application_path = os.path.dirname(sys.executable)
            else:
                # 如果是普通Python脚本，使用脚本所在目录
                application_path = os.path.dirname(os.path.abspath(__file__))
            
            # 数据库文件保存在应用程序目录下
            self.db_path = os.path.join(application_path, db_name)
            print(f"数据库路径: {self.db_path}")
        except Exception as e:
            # 如果出错，回退到当前工作目录
            self.db_path = os.path.join(os.getcwd(), db_name)
            print(f"获取应用路径出错，使用当前工作目录: {self.db_path}, 错误: {str(e)}")
        
        self.conn = None
        self.cursor = None
        self.connected = False
        
        # 创建数据库连接，使用check_same_thread=False允许在不同线程中使用
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.cursor = self.conn.cursor()
            self.connected = True
            
            # 创建数据表
            self.create_tables()
            
            print(f"数据库连接成功: {self.db_path}")
        except sqlite3.Error as e:
            print(f"数据库连接错误: {str(e)}")
    
    def create_tables(self):
        """创建必要的数据表"""
        if not self.connected:
            return
            
        try:
            # 创建周期数据表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS cycle_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    cycle_number INTEGER NOT NULL,
                    data BLOB NOT NULL
                )
            ''')
            
            # 创建原始数据表
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS raw_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    broker TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    raw_data BLOB NOT NULL
                )
            ''')
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"创建数据表错误: {str(e)}")
    
    def save_cycle_data(self, cycle_number, data):
        """保存周期数据"""
        if not self.connected:
            return
            
        try:
            # 将数据列表转换为字符串存储
            data_str = ','.join(map(str, data))
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            
            self.cursor.execute(
                "INSERT INTO cycle_data (timestamp, cycle_number, data) VALUES (?, ?, ?)",
                (timestamp, cycle_number, data_str)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"保存周期数据错误: {str(e)}")
            return False
    
    def save_raw_data(self, broker, topic, raw_data):
        """保存原始数据"""
        if not self.connected:
            return
            
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
            
            self.cursor.execute(
                "INSERT INTO raw_data (timestamp, broker, topic, raw_data) VALUES (?, ?, ?, ?)",
                (timestamp, broker, topic, raw_data)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"保存原始数据错误: {str(e)}")
            return False
    
    def get_cycle_data(self, limit=100, offset=0):
        """获取周期数据"""
        if not self.connected:
            return []
            
        try:
            self.cursor.execute(
                "SELECT * FROM cycle_data ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"获取周期数据错误: {str(e)}")
            return []
    
    def get_raw_data(self, limit=100, offset=0):
        """获取原始数据"""
        if not self.connected:
            return []
            
        try:
            self.cursor.execute(
                "SELECT * FROM raw_data ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"获取原始数据错误: {str(e)}")
            return []
    
    def get_cycle_count(self):
        """获取周期数据总数"""
        if not self.connected:
            return 0
            
        try:
            self.cursor.execute("SELECT COUNT(*) FROM cycle_data")
            return self.cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"获取周期数据总数错误: {str(e)}")
            return 0
    
    def get_raw_count(self):
        """获取原始数据总数"""
        if not self.connected:
            return 0
            
        try:
            self.cursor.execute("SELECT COUNT(*) FROM raw_data")
            return self.cursor.fetchone()[0]
        except sqlite3.Error as e:
            print(f"获取原始数据总数错误: {str(e)}")
            return 0
    
    def get_latest_cycle_data(self, count=1):
        """获取最新的周期数据"""
        if not self.connected:
            return []
            
        try:
            self.cursor.execute(
                "SELECT * FROM cycle_data ORDER BY timestamp DESC LIMIT ?",
                (count,)
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"获取最新周期数据错误: {str(e)}")
            return []
    
    def get_cycle_data_by_time(self, start_time, end_time):
        """根据时间范围获取周期数据"""
        if not self.connected:
            return []
            
        try:
            self.cursor.execute(
                "SELECT * FROM cycle_data WHERE timestamp BETWEEN ? AND ? ORDER BY timestamp",
                (start_time, end_time)
            )
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"根据时间范围获取周期数据错误: {str(e)}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if self.connected:
            try:
                self.conn.close()
                self.connected = False
                print("数据库连接已关闭")
            except sqlite3.Error as e:
                print(f"关闭数据库连接错误: {str(e)}")

class MplCanvas(FigureCanvas):
    """Matplotlib画布类，用于在Qt界面中嵌入matplotlib图形"""
    def __init__(self, parent=None, width=10, height=4, dpi=100, with_3d=True, unit_label="幅值 (mV)"):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        
        # 创建左右两个子图
        if with_3d:
            self.axes_2d = self.fig.add_subplot(121)  # 左侧2D图
            self.axes_3d = self.fig.add_subplot(122, projection='3d')  # 右侧3D图
        else:
            self.axes_2d = self.fig.add_subplot(111)  # 只有2D图
            self.axes_3d = None
            
        super(MplCanvas, self).__init__(self.fig)
        self.fig.tight_layout()
        
        # 设置动画效果
        self.blit = False
        self.axes_2d.grid(True, linestyle='--', alpha=0.7)
        self.scatter = None
        self.line = None
        
        # 3D图设置
        if self.axes_3d:
            self.axes_3d.set_title("PRPS图")
            self.axes_3d.set_xlabel("相位")
            self.axes_3d.set_ylabel("周期")
            self.axes_3d.set_zlabel(unit_label)
            self.surface = None

class MQTTThread(QThread):
    """MQTT处理线程，避免阻塞主线程"""
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.running = True
        self.mutex = QMutex()  # 添加互斥锁保护running变量
        
    def run(self):
        while True:
            self.mutex.lock()
            if not self.running:
                self.mutex.unlock()
                break
            self.mutex.unlock()
            
            try:
                self.client.loop(0.1)  # 非阻塞处理MQTT消息
            except Exception as e:
                print(f"MQTT线程错误: {str(e)}")
                
            time.sleep(0.01)  # 避免CPU占用过高
            
    def stop(self):
        self.mutex.lock()
        self.running = False
        self.mutex.unlock()
        # 确保线程能够退出循环
        self.client.loop_stop()

class MQTTClient(QWidget):
    """MQTT客户端类，处理MQTT连接和消息接收"""
    message_received = Signal(list)  # 信号：接收到新消息时发出
    connection_status = Signal(bool, str)  # 信号：连接状态变化时发出
    raw_data_received = Signal(str, str, str)  # 信号：接收到原始数据时发出，传递broker、topic和数据

    def __init__(self):
        super().__init__()
        self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        
        self.broker_address = "192.168.16.135"
        self.broker_port = 1883
        self.topic = "pub1"
        self.connected = False
        self.mqtt_thread = None
        self.message_queue = queue.Queue(maxsize=10)  # 限制队列大小，避免内存溢出
        
        # 数据库管理器
        self.db_manager = None
        
        # 创建一个定时器来处理消息队列
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self.process_message_queue)
        self.queue_timer.start(50)  # 每50ms处理一次队列

    def set_database_manager(self, db_manager):
        """设置数据库管理器"""
        self.db_manager = db_manager

    def connect_to_broker(self, broker_address, broker_port, topic):
        """连接到MQTT Broker"""
        # 如果已经连接，先断开
        if self.connected:
            self.disconnect_from_broker()
            
        self.broker_address = broker_address
        self.broker_port = int(broker_port)
        self.topic = topic
        
        try:
            # 重新创建MQTT客户端，确保状态干净
            self.client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            self.client.on_disconnect = self.on_disconnect
            
            # 连接到Broker
            self.client.connect(self.broker_address, self.broker_port)
            
            # 重新启动消息队列处理定时器
            if hasattr(self, 'queue_timer') and not self.queue_timer.isActive():
                self.queue_timer.start(50)
                
            # 使用线程处理MQTT消息循环，避免阻塞主线程
            if self.mqtt_thread is None or not self.mqtt_thread.isRunning():
                self.mqtt_thread = MQTTThread(self.client)
                self.mqtt_thread.start()
                
            return True
        except Exception as e:
            self.connection_status.emit(False, f"连接失败: {str(e)}")
            return False

    def disconnect_from_broker(self):
        """断开与MQTT Broker的连接"""
        try:
            # 先将连接状态设置为断开
            self.connected = False
            
            # 停止消息队列处理定时器
            if hasattr(self, 'queue_timer') and self.queue_timer.isActive():
                self.queue_timer.stop()
            
            # 清空消息队列
            while not self.message_queue.empty():
                try:
                    self.message_queue.get_nowait()
                    self.message_queue.task_done()
                except queue.Empty:
                    break
            
            # 停止MQTT消息处理线程
            if self.mqtt_thread and self.mqtt_thread.isRunning():
                self.mqtt_thread.stop()
                # 等待线程结束，但最多等待1秒
                if not self.mqtt_thread.wait(1000):
                    print("MQTT线程停止超时")
                self.mqtt_thread = None
            
            # 断开MQTT连接，但不等待回调
            try:
                if hasattr(self.client, '_sock') and self.client._sock:
                    self.client.disconnect()
                    # 确保完全断开连接
                    self.client.loop_stop()
            except Exception as e:
                print(f"断开MQTT连接时发生错误: {str(e)}")
                
            # 发出连接状态信号
            self.connection_status.emit(False, "已断开连接")
        
        except Exception as e:
            print(f"断开连接时发生错误: {str(e)}")
            self.connection_status.emit(False, f"断开连接失败: {str(e)}")

    def on_connect(self, client, userdata, flags, rc, properties):
        """连接回调函数"""
        if rc == 0:
            self.connected = True
            client.subscribe(self.topic, qos=1)
            self.connection_status.emit(True, f"已连接到 {self.broker_address}:{self.broker_port}")
        else:
            self.connected = False
            self.connection_status.emit(False, f"连接失败，返回码: {rc}")

    def on_disconnect(self, client, userdata, rc, properties=None, *args):
        """断开连接回调函数"""
        self.connected = False
        self.connection_status.emit(False, "已断开连接")

    def process_message_queue(self):
        """处理消息队列"""
        if not self.message_queue.empty():
            try:
                data = self.message_queue.get_nowait()
                self.message_received.emit(data)
                self.message_queue.task_done()
            except queue.Empty:
                pass

    def on_message(self, client, userdata, msg):
        """消息接收回调函数"""
        try:
            hex_message = msg.payload.hex()  # 解码消息内容为十六进制字符串
            
            # 发出原始数据信号，让主线程处理数据库保存
            if hasattr(self, 'db_manager') and self.db_manager is not None:
                # 使用信号将原始数据发送到主线程，而不是直接在MQTT线程中保存
                self.raw_data_received.emit(self.broker_address, self.topic, hex_message)
                
            results = []
            for i in range(0, len(hex_message), 4):  # 每4个字符解析为一个16进制数
                if i + 4 <= len(hex_message):
                    hex_value = hex_message[i:i+4]
                    decimal_value = int(hex_value, 16)
                    converted_value = decimal_value * 3.3 / 4096
                    results.append(round(converted_value, 2))  # 保留两位小数
            
            meaningful_data = results[4:-1]  # 去掉前4个和最后一个数据
            
            # 将数据放入队列，而不是直接发送信号
            # 如果队列已满，则丢弃这条消息，避免处理积压
            try:
                self.message_queue.put_nowait(meaningful_data)
            except queue.Full:
                pass
                
        except Exception as e:
            print(f"消息处理错误: {str(e)}")

class DatabaseViewDialog(QDialog):
    """数据库查看对话框"""
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("数据库数据查看")
        self.setMinimumSize(800, 600)
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 创建查询选项组
        query_group = QGroupBox("查询选项")
        query_layout = QGridLayout()
        
        # 添加数据类型选择
        query_layout.addWidget(QLabel("数据类型:"), 0, 0)
        self.data_type_combo = QComboBox()
        self.data_type_combo.addItems(["周期数据", "原始数据"])
        query_layout.addWidget(self.data_type_combo, 0, 1)
        
        # 添加查询类型选择
        query_layout.addWidget(QLabel("查询类型:"), 0, 2)
        self.query_type_combo = QComboBox()
        self.query_type_combo.addItems(["最新数据", "按时间范围"])
        self.query_type_combo.currentIndexChanged.connect(self.toggle_query_mode)
        query_layout.addWidget(self.query_type_combo, 0, 3)
        
        # 添加最新数据数量选择
        query_layout.addWidget(QLabel("最新数据数量:"), 1, 0)
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 1000)
        self.limit_spin.setValue(100)
        query_layout.addWidget(self.limit_spin, 1, 1)
        
        # 添加开始时间选择
        query_layout.addWidget(QLabel("开始时间:"), 1, 2)
        self.start_time_edit = QDateTimeEdit()
        self.start_time_edit.setDateTime(QDateTime.currentDateTime().addDays(-1))  # 默认为当前时间的前一天
        self.start_time_edit.setCalendarPopup(True)
        self.start_time_edit.setEnabled(False)  # 默认禁用
        query_layout.addWidget(self.start_time_edit, 1, 3)
        
        # 添加结束时间选择
        query_layout.addWidget(QLabel("结束时间:"), 1, 4)
        self.end_time_edit = QDateTimeEdit()
        self.end_time_edit.setDateTime(QDateTime.currentDateTime())  # 默认为当前时间
        self.end_time_edit.setCalendarPopup(True)
        self.end_time_edit.setEnabled(False)  # 默认禁用
        query_layout.addWidget(self.end_time_edit, 1, 5)
        
        # 添加查询按钮
        self.query_button = QPushButton("查询")
        self.query_button.clicked.connect(self.query_data)
        query_layout.addWidget(self.query_button, 0, 5)
        
        # 添加查看PRPD/PRPS图按钮 (只对周期数据有效)
        self.generate_prpd_button = QPushButton("查看PRPD/PRPS图")
        self.generate_prpd_button.clicked.connect(self.view_historical_charts)
        query_layout.addWidget(self.generate_prpd_button, 1, 6)
        
        query_group.setLayout(query_layout)
        layout.addWidget(query_group)
        
        # 创建数据表格
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.show_data_details)
        layout.addWidget(self.table)
        
        # 创建状态标签
        self.status_label = QLabel()
        layout.addWidget(self.status_label)
        
        # 存储查询结果
        self.query_results = []
        
        # 初始查询
        self.query_data()
    
    def toggle_query_mode(self, index):
        """切换查询模式"""
        is_time_range = (index == 1)
        self.start_time_edit.setEnabled(is_time_range)
        self.end_time_edit.setEnabled(is_time_range)
        self.limit_spin.setEnabled(not is_time_range)
    
    def view_historical_charts(self):
        """从历史数据生成PRPD或PRPS图"""
        # 确保数据类型是周期数据
        if self.data_type_combo.currentText() != "周期数据" or not self.query_results:
            QMessageBox.warning(self, "无法生成图表", "请先查询周期数据，并确保有查询结果。")
            return
        
        # 创建新的对话框显示历史数据可视化
        dialog = HistoricalChartsDialog(self.query_results, self)
        dialog.exec()
    
    def show_data_details(self, index):
        """显示数据详情"""
        row = index.row()
        if row < 0 or row >= len(self.query_results):
            return
            
        # 获取数据
        data_row = self.query_results[row]
        data_type = self.data_type_combo.currentText()
        
        # 创建详情对话框
        detail_dialog = QDialog(self)
        detail_dialog.setWindowTitle("数据详情")
        detail_dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(detail_dialog)
        
        if data_type == "周期数据":
            # 显示周期数据详情
            id_label = QLabel(f"ID: {data_row[0]}")
            timestamp_label = QLabel(f"时间戳: {data_row[1]}")
            cycle_label = QLabel(f"周期编号: {data_row[2]}")
            
            layout.addWidget(id_label)
            layout.addWidget(timestamp_label)
            layout.addWidget(cycle_label)
            
            # 显示数据
            data_group = QGroupBox("数据内容")
            data_layout = QVBoxLayout()
            
            data_str = data_row[3]
            data_points = data_str.split(',')
            
            # 创建数据表格
            data_table = QTableWidget()
            data_table.setColumnCount(2)
            data_table.setHorizontalHeaderLabels(["序号", "值"])
            data_table.setRowCount(len(data_points))
            
            for i, point in enumerate(data_points):
                data_table.setItem(i, 0, QTableWidgetItem(str(i)))
                data_table.setItem(i, 1, QTableWidgetItem(point))
            
            data_layout.addWidget(data_table)
            data_group.setLayout(data_layout)
            layout.addWidget(data_group)
            
        else:  # 原始数据
            # 显示原始数据详情
            id_label = QLabel(f"ID: {data_row[0]}")
            timestamp_label = QLabel(f"时间戳: {data_row[1]}")
            broker_label = QLabel(f"Broker: {data_row[2]}")
            topic_label = QLabel(f"主题: {data_row[3]}")
            
            layout.addWidget(id_label)
            layout.addWidget(timestamp_label)
            layout.addWidget(broker_label)
            layout.addWidget(topic_label)
            
            # 显示原始数据
            data_group = QGroupBox("原始数据")
            data_layout = QVBoxLayout()
            
            raw_data = str(data_row[4])
            data_text = QLabel(raw_data)
            data_text.setWordWrap(True)
            data_text.setTextInteractionFlags(Qt.TextSelectableByMouse)
            
            # 添加滚动区域
            scroll_area = QWidget()
            scroll_layout = QVBoxLayout(scroll_area)
            scroll_layout.addWidget(data_text)
            scroll_layout.addStretch()
            
            scroll = QScrollArea()
            scroll.setWidget(scroll_area)
            scroll.setWidgetResizable(True)
            
            data_layout.addWidget(scroll)
            data_group.setLayout(data_layout)
            layout.addWidget(data_group)
        
        # 添加关闭按钮
        close_button = QPushButton("关闭")
        close_button.clicked.connect(detail_dialog.accept)
        layout.addWidget(close_button)
        
        detail_dialog.exec()
    
    def query_data(self):
        """根据选择的选项查询数据"""
        data_type = self.data_type_combo.currentText()
        query_type = self.query_type_combo.currentText()
        limit = self.limit_spin.value()
        
        # 获取时间范围
        start_time = self.start_time_edit.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        end_time = self.end_time_edit.dateTime().toString("yyyy-MM-dd hh:mm:ss")
        
        # 清空表格和结果
        self.table.clear()
        self.table.setRowCount(0)
        self.query_results = []
        
        if not self.db_manager or not self.db_manager.connected:
            self.status_label.setText("数据库未连接")
            return
        
        try:
            # 根据数据类型查询
            if data_type == "周期数据":
                # 设置表头
                self.table.setColumnCount(4)
                self.table.setHorizontalHeaderLabels(["ID", "时间戳", "周期编号", "数据(前10个点)"])
                
                # 查询数据
                data = []
                if query_type == "最新数据":
                    data = self.db_manager.get_latest_cycle_data(limit)
                else:  # 按时间范围
                    data = self.db_manager.get_cycle_data_by_time(start_time, end_time)
                
                # 保存查询结果
                self.query_results = data
                
                # 填充表格
                self.table.setRowCount(len(data))
                for i, row in enumerate(data):
                    self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                    self.table.setItem(i, 1, QTableWidgetItem(str(row[1])))
                    self.table.setItem(i, 2, QTableWidgetItem(str(row[2])))
                    
                    # 显示数据的前10个点
                    data_str = row[3]
                    data_points = data_str.split(',')
                    preview = ','.join(data_points[:10])
                    if len(data_points) > 10:
                        preview += "..."
                    self.table.setItem(i, 3, QTableWidgetItem(preview))
                
                self.status_label.setText(f"已查询到 {len(data)} 条周期数据")
            
            else:  # 原始数据
                # 设置表头
                self.table.setColumnCount(5)
                self.table.setHorizontalHeaderLabels(["ID", "时间戳", "Broker", "主题", "原始数据(前30个字符)"])
                
                # 查询数据
                data = self.db_manager.get_raw_data(limit)
                
                # 保存查询结果
                self.query_results = data
                
                # 填充表格
                self.table.setRowCount(len(data))
                for i, row in enumerate(data):
                    self.table.setItem(i, 0, QTableWidgetItem(str(row[0])))
                    self.table.setItem(i, 1, QTableWidgetItem(str(row[1])))
                    self.table.setItem(i, 2, QTableWidgetItem(str(row[2])))
                    self.table.setItem(i, 3, QTableWidgetItem(str(row[3])))
                    
                    # 显示原始数据的前30个字符
                    raw_data = str(row[4])
                    preview = raw_data[:30]
                    if len(raw_data) > 30:
                        preview += "..."
                    self.table.setItem(i, 4, QTableWidgetItem(preview))
                
                self.status_label.setText(f"已查询到 {len(data)} 条原始数据")
            
            # 调整列宽
            self.table.resizeColumnsToContents()
            
        except Exception as e:
            self.status_label.setText(f"查询数据错误: {str(e)}")

class HistoricalChartsDialog(QDialog):
    """历史数据可视化对话框"""
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("历史数据可视化")
        self.setMinimumSize(1000, 700)  # 增加对话框尺寸以容纳3D图
        self.data = data
        
        # 单位设置
        self.use_dbm = False  # 默认使用毫伏(mV)单位
        self.unit_label = "幅值 (mV)"  # 默认单位标签
        
        # PRPS图设置
        self.prps_max_cycles = 50  # PRPS图固定显示最新的50个周期
        
        # 创建布局
        layout = QVBoxLayout(self)
        
        # 创建设置组
        settings_group = QGroupBox("图表设置")
        settings_layout = QGridLayout()
        
        # 添加图表类型选择
        settings_layout.addWidget(QLabel("图表类型:"), 0, 0)
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["PRPD散点图", "PRPD线图", "PRPS三维图"])
        self.chart_type_combo.currentIndexChanged.connect(self.update_chart)
        settings_layout.addWidget(self.chart_type_combo, 0, 1)
        
        # 添加数据范围选择
        settings_layout.addWidget(QLabel("数据范围:"), 0, 2)
        self.range_spin = QSpinBox()
        self.range_spin.setRange(1, len(self.data))
        self.range_spin.setValue(min(50, len(self.data)))  # 默认显示50个周期或全部
        self.range_spin.valueChanged.connect(self.update_chart)
        settings_layout.addWidget(self.range_spin, 0, 3)
        settings_layout.addWidget(QLabel(f"/ {len(self.data)} 周期"), 0, 4)
        
        # 添加显示参考正弦波选项
        self.show_sine_checkbox = QCheckBox("显示参考正弦波")
        self.show_sine_checkbox.setChecked(True)
        self.show_sine_checkbox.stateChanged.connect(self.update_chart)
        settings_layout.addWidget(self.show_sine_checkbox, 1, 0)
        
        # 添加正弦波振幅设置
        settings_layout.addWidget(QLabel("正弦波振幅:"), 1, 1)
        self.sine_amplitude_spin = QDoubleSpinBox()
        self.sine_amplitude_spin.setRange(0.1, 3.0)
        self.sine_amplitude_spin.setValue(1.0)
        self.sine_amplitude_spin.setSingleStep(0.1)
        self.sine_amplitude_spin.valueChanged.connect(self.update_chart)
        settings_layout.addWidget(self.sine_amplitude_spin, 1, 2)
        
        # 添加单位转换按钮
        self.unit_button = QPushButton("单位: mV")
        self.unit_button.clicked.connect(self.toggle_unit)
        settings_layout.addWidget(self.unit_button, 1, 3)
        
        # 添加PRPS颜色方案选择
        settings_layout.addWidget(QLabel("PRPS颜色方案:"), 2, 0)
        self.color_scheme_combo = QComboBox()
        # 定义颜色方案
        self.color_schemes = {
            "默认方案": ['#000000', '#FFFFFE', '#FFFF13', '#FF0000'],
            "蓝绿红": ['#0000FF', '#00FFFF', '#00FF00', '#FF0000'],
            "黑蓝紫": ['#000000', '#0000FF', '#800080', '#FF00FF'],
            "绿黄红": ['#006400', '#7FFF00', '#FFFF00', '#FF0000']
        }
        self.color_scheme_combo.addItems(list(self.color_schemes.keys()))
        self.color_scheme_combo.setCurrentText("默认方案")
        self.color_scheme_combo.currentTextChanged.connect(self.update_chart)
        settings_layout.addWidget(self.color_scheme_combo, 2, 1)
        
        # 添加导出图像按钮
        self.export_button = QPushButton("导出图像")
        self.export_button.clicked.connect(self.export_image)
        settings_layout.addWidget(self.export_button, 2, 4)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # 创建matplotlib画布
        self.canvas_widget = QWidget()
        canvas_layout = QVBoxLayout(self.canvas_widget)
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        canvas_layout.addWidget(self.canvas)
        layout.addWidget(self.canvas_widget)
        
        # 添加关闭按钮
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        layout.addWidget(self.close_button)
        
        # 初始化图表相关变量
        self.axes_2d = None
        self.axes_3d = None
        self.colorbar = None
        
        # 绘制初始图表
        self.update_chart()
    
    def toggle_unit(self):
        """切换单位显示（毫伏mV和dBm）"""
        self.use_dbm = not self.use_dbm
        
        if self.use_dbm:
            self.unit_button.setText("单位: dBm")
            self.unit_label = "幅值 (dBm)"
        else:
            self.unit_button.setText("单位: mV")
            self.unit_label = "幅值 (mV)"
        
        # 更新图表
        self.update_chart()
    
    def convert_unit(self, value, to_dbm=True):
        """转换单位
        
        Args:
            value: 要转换的值
            to_dbm: 如果为True，将毫伏转换为dBm；如果为False，将dBm转换为毫伏
            
        Returns:
            转换后的值
        """
        if to_dbm:
            # 毫伏转dBm: 毫伏值*54.545-81.818
            return value * 54.545 - 81.818
        else:
            # dBm转毫伏: (dBm值+81.818)/54.545
            return (value + 81.818) / 54.545
    
    def create_custom_colormap(self, colors):
        """
        根据给定的颜色列表创建自定义颜色映射
        
        :param colors: 颜色列表，至少包含4种颜色
        :return: matplotlib颜色映射对象
        """
        import matplotlib.colors as mcolors
        import matplotlib.pyplot as plt
        
        # 确保有足够的颜色
        if len(colors) < 4:
            colors = colors + ['#FF0000']  # 默认添加红色
        
        # 创建颜色映射
        n_bins = 100  # 颜色渐变的细腻程度
        cmap = mcolors.LinearSegmentedColormap.from_list(
            'custom_colormap', 
            [mcolors.to_rgba(color) for color in colors[:4]], 
            N=n_bins
        )
        
        return cmap
    
    def update_chart(self):
        """更新图表"""
        # 获取设置
        chart_type = self.chart_type_combo.currentText()
        data_range = self.range_spin.value()
        show_sine_wave = self.show_sine_checkbox.isChecked()
        sine_amplitude = self.sine_amplitude_spin.value()
        color_scheme = self.color_scheme_combo.currentText()
        
        # 确保数据范围不超过实际数据量
        data_range = min(data_range, len(self.data))
        
        # 从查询结果中准备数据
        all_data = []
        cycle_labels = []
        
        # 只使用最新的N个数据点（根据范围设置）
        selected_data = self.data[-data_range:]
        
        for row in selected_data:
            # 周期数据存储在第3列(索引为2)
            cycle_number = row[2]
            cycle_labels.append(f"周期 {cycle_number}")
            
            # 数据字符串存储在第4列(索引为3)
            data_str = row[3]
            data_points = [float(point) for point in data_str.split(',')]
            all_data.append(data_points)
        
        # 清除当前图表并重新创建
        self.figure.clear()
        
        # 移除之前的颜色条
        if hasattr(self, 'colorbar') and self.colorbar is not None:
            try:
                self.colorbar.remove()
            except:
                pass
            self.colorbar = None
        
        if chart_type == "PRPS三维图":
            # 创建3D图
            self.axes_3d = self.figure.add_subplot(111, projection='3d')
            self.draw_prps(all_data, cycle_labels, color_scheme)
        else:
            # 创建2D图
            self.axes_2d = self.figure.add_subplot(111)
            self.draw_prpd(all_data, cycle_labels, chart_type, show_sine_wave, sine_amplitude)
        
        # 重绘画布
        self.figure.tight_layout()
        self.canvas.draw()
    
    def draw_prpd(self, all_data, cycle_labels, chart_type, show_sine_wave, sine_amplitude):
        """绘制PRPD图"""
        if not all_data:
            self.axes_2d.text(0.5, 0.5, "没有数据可显示", ha='center', va='center')
            return
            
        # 合并所有周期的数据用于绘图
        flattened_data = []
        x_data = []
        
        for i, cycle_data in enumerate(all_data):
            cycle_phases = np.linspace(0, 360, len(cycle_data))
            flattened_data.extend(cycle_data)
            x_data.extend(cycle_phases)
        
        # 根据当前单位设置转换数据
        if self.use_dbm:
            display_data = []
            for cycle_data in all_data:
                display_data.append([self.convert_unit(x, True) for x in cycle_data])
            
            # 合并所有周期的转换后数据
            all_display_data = []
            for cycle_data in display_data:
                all_display_data.extend(cycle_data)
        else:
            display_data = all_data
            all_display_data = flattened_data
        
        if chart_type == "PRPD散点图":
            self.axes_2d.scatter(x_data, all_display_data, alpha=0.7, s=10)
        elif chart_type == "PRPD线图":
            # 对于线图，按周期分别绘制
            for i, cycle_data in enumerate(display_data):
                cycle_phases = np.linspace(0, 360, len(cycle_data))
                # 仅当周期数不多时显示图例
                if len(display_data) <= 10:
                    self.axes_2d.plot(cycle_phases, cycle_data, linewidth=1.0, 
                              label=cycle_labels[i])
                else:
                    self.axes_2d.plot(cycle_phases, cycle_data, linewidth=1.0)
            
            # 如果周期数较少，添加图例
            if len(display_data) <= 10:
                self.axes_2d.legend(loc='upper right')
        
        # 绘制参考正弦波
        if show_sine_wave:
            # 确定数据的振幅范围，用于缩放正弦波
            if all_display_data:
                max_data = max(all_display_data)
                min_data = min(all_display_data)
                data_range = max_data - min_data
                # 计算正弦波的振幅，使其与数据的振幅范围相适应
                sine_amp = sine_amplitude * data_range / 4
                # 计算正弦波的偏移量，使其居中显示
                sine_offset = (max_data + min_data) / 2
            else:
                sine_amp = sine_amplitude
                sine_offset = 0
            
            # 生成正弦波数据
            x_sine = np.linspace(0, 360, 1000)
            y_sine = sine_amp * np.sin(x_sine * 2 * np.pi / 360) + sine_offset
            
            # 绘制正弦波
            self.axes_2d.plot(x_sine, y_sine, 'r-', linewidth=1.5, alpha=0.7, label="参考正弦波")
        
        # 设置图表标题和轴标签
        self.axes_2d.set_title(f"PRPD图 ({len(all_data)}个周期)")
        self.axes_2d.set_xlabel("相位 )")
        self.axes_2d.set_ylabel(self.unit_label)
        
        # 设置网格
        self.axes_2d.grid(True, linestyle='--', alpha=0.7)
    
    def draw_prps(self, all_data, cycle_labels, color_scheme):
        """绘制PRPS三维图"""
        # 清除当前3D图并重新创建
        self.figure.delaxes(self.axes_3d)
        self.axes_3d = self.figure.add_subplot(111, projection='3d')
        
        # 移除之前的颜色条
        try:
            if hasattr(self.canvas, 'colorbar'):
                # 尝试安全地移除颜色条
                self.canvas.colorbar.remove()
                delattr(self.canvas, 'colorbar')
        except Exception:
            # 如果移除失败，直接忽略
            pass
        
        # 只使用PRPS需要的最新周期数
        prps_data = all_data[-self.prps_max_cycles:] if len(all_data) > self.prps_max_cycles else all_data
        
        # 准备数据
        num_cycles = len(prps_data)
        if num_cycles == 0:
            return
            
        # 找到所有周期中最大的数据点数
        max_points = max(len(cycle_data) for cycle_data in prps_data)
        
        # 创建规则网格
        phase = np.linspace(0, 360, max_points)
        cycles = np.arange(1, num_cycles + 1)
        
        # 创建空的Z值矩阵
        z_data = np.zeros((num_cycles, max_points))
        
        # 填充Z值矩阵
        for i, cycle_data in enumerate(prps_data):
            # 对于每个周期，我们需要将数据重采样到max_points个点
            if len(cycle_data) == max_points:
                z_data[i, :] = cycle_data
            else:
                # 如果周期的数据点数不等于max_points，则需要重采样
                cycle_phases = np.linspace(0, 360, len(cycle_data))
                z_data[i, :] = np.interp(phase, cycle_phases, cycle_data)
        
        # 根据当前单位设置转换数据
        if self.use_dbm:
            # 转换z_data中的每个值
            for i in range(z_data.shape[0]):
                for j in range(z_data.shape[1]):
                    z_data[i, j] = self.convert_unit(z_data[i, j], True)
        
        # 创建网格
        X, Y = np.meshgrid(phase, cycles)
        
        # 创建自定义颜色映射
        custom_cmap = self.create_custom_colormap(self.color_schemes[color_scheme])
        
        # 绘制3D表面
        surf = self.axes_3d.plot_surface(X, Y, z_data, cmap=custom_cmap, 
                                           edgecolor='none', alpha=0.8)
        
        # 添加颜色条，并将其保存为实例属性
        self.colorbar = self.figure.colorbar(surf, ax=self.axes_3d, shrink=0.5, aspect=5)
        
        # 设置图表标题和轴标签
        self.axes_3d.set_title(f"历史PRPS图 ({num_cycles}个周期)")
        self.axes_3d.set_xlabel("相位)")
        self.axes_3d.set_ylabel("周期")
        self.axes_3d.set_zlabel(self.unit_label)
        
        # 强制设置坐标轴范围和刻度
        self.axes_3d.set_xlim(0, 360)  # 相位范围固定为0-360度
        self.axes_3d.set_ylim(1, num_cycles)  # 周期范围
        
        # 设置Z轴范围（根据数据动态调整，但保持一定的稳定性）
        z_min = np.min(z_data) - 0.1 * (np.max(z_data) - np.min(z_data))  # 确保有足够的下边界空间
        z_max = np.max(z_data) + 0.1 * (np.max(z_data) - np.min(z_data))  # 确保有足够的上边界空间
        
        # 针对dBm单位进行特殊处理
        if self.use_dbm:
            # 对于dBm单位，我们可能需要更宽的范围
            # 确保最小值不会太小，避免显示大量无意义的空白区域
            if z_min < -80:
                z_min = -80  # dBm的一个合理下限
            
            # 确保范围足够宽以显示有意义的数据
            if z_max - z_min < 20:
                z_mean = (z_max + z_min) / 2
                z_min = z_mean - 10
                z_max = z_mean + 10
        else:
            # 对于毫伏单位，确保最小值不低于0（物理上有意义）
            if z_min < 0:
                z_min = 0
        
        self.axes_3d.set_zlim(z_min, z_max)
        
        # 设置视角和投影方式
        self.axes_3d.view_init(elev=30, azim=270)
        self.axes_3d.set_box_aspect((1.5, 1, 0.8))  # 固定图形纵横比
    
    def export_image(self):
        """导出图表为图像文件"""
        try:
            # 获取保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出图像", "", "PNG文件 (*.png);;JPEG文件 (*.jpg);;所有文件 (*.*)"
            )
            
            if file_path:
                self.figure.savefig(file_path, dpi=300, bbox_inches='tight')
                QMessageBox.information(self, "导出成功", f"图像已保存到:\n{file_path}")
        except Exception as e:
            QMessageBox.warning(self, "导出失败", f"导出图像时发生错误:\n{str(e)}")

class MainWindow(QMainWindow):
    """主窗口类"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GIS局部放电在线监测系统")
        self.setMinimumSize(1200, 700)  # 增加窗口宽度以适应两个子图
        
        # 预定义颜色方案
        self.color_schemes = {
            "默认方案": ['#000000', '#FFFFFE', '#FFFF13', '#FF0000'],
            "蓝绿红": ['#0000FF', '#00FFFF', '#00FF00', '#FF0000'],
            "黑蓝紫": ['#000000', '#0000FF', '#800080', '#FF00FF'],
            "绿黄红": ['#006400', '#7FFF00', '#FFFF00', '#FF0000']
        }
        
        # 当前选择的颜色方案
        self.current_color_scheme = "默认方案"
        
        # 数据存储
        self.data_buffer = []
        self.max_buffer_size = 360  # 默认缓冲区大小
        self.data_mutex = QMutex()  # 用于线程安全访问数据
        self.last_update_time = time.time()
        self.update_interval = 0.2  # 控制更新频率，每0.2秒更新一次
        
        # 周期数据存储
        self.cycle_count = 1  # 当前周期计数
        self.max_cycles = 50  # 默认最大周期数，用于PRPD图
        self.prps_max_cycles = 50  # PRPS图固定显示最新的50个周期
        self.accumulated_data = []  # 累积的数据
        
        # CSV导出设置
        self.csv_export_cycles = 50  # 默认导出50个周期数据
        
        # 自动保存图像设置
        self.auto_save_images = False  # 默认不自动保存
        self.image_save_interval = 5000  # 保存间隔，单位毫秒(5秒)
        self.last_image_save_time = time.time()
        
        # 显示设置
        self.show_3d_plot = True  # 是否显示3D图
        self.show_sine_wave = True  # 是否显示参考正弦波
        self.sine_amplitude = 1.0  # 参考正弦波振幅
        
        # 单位设置
        self.use_dbm = False  # 默认使用毫伏(mV)单位
        self.unit_label = "幅值 (mV)"  # 默认单位标签
        
        # 数据库设置
        self.save_to_db = False  # 默认不保存数据到数据库
        self.db_manager = DatabaseManager()  # 创建数据库管理器
        
        # 获取保存路径信息
        self.get_save_paths()
        
        # 创建MQTT客户端
        self.mqtt_client = MQTTClient()
        self.mqtt_client.set_database_manager(self.db_manager)  # 设置数据库管理器
        self.mqtt_client.message_received.connect(self.update_plot)
        self.mqtt_client.connection_status.connect(self.update_connection_status)
        self.mqtt_client.raw_data_received.connect(self.save_raw_data)  # 连接原始数据信号
        
        # 创建界面
        self.setup_ui()
        
        # 创建定时器用于更新界面
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(1000)  # 每秒更新一次状态
        
        # 创建定时器用于限制绘图频率
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.redraw_plot)
        self.plot_timer.start(200)  # 每200ms重绘一次图表
        
        # 创建定时器用于自动保存图像
        self.image_save_timer = QTimer()
        self.image_save_timer.timeout.connect(self.auto_save_image)
        # 定时器默认不启动，等待用户勾选
        
        # 标记是否需要重绘
        self.need_redraw = False
    
    def setup_ui(self):
        """设置用户界面"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 创建连接设置组
        connection_group = QGroupBox("MQTT连接设置")
        connection_layout = QGridLayout()
        
        # 添加Broker地址设置
        connection_layout.addWidget(QLabel("Broker地址:"), 0, 0)
        self.broker_address_input = QLineEdit(self.mqtt_client.broker_address)
        connection_layout.addWidget(self.broker_address_input, 0, 1)
        
        # 添加Broker端口设置
        connection_layout.addWidget(QLabel("Broker端口:"), 0, 2)
        self.broker_port_input = QLineEdit(str(self.mqtt_client.broker_port))
        connection_layout.addWidget(self.broker_port_input, 0, 3)
        
        # 添加主题设置
        connection_layout.addWidget(QLabel("主题:"), 1, 0)
        self.topic_input = QLineEdit(self.mqtt_client.topic)
        connection_layout.addWidget(self.topic_input, 1, 1)
        
        # 添加连接按钮
        self.connect_button = QPushButton("连接")
        self.connect_button.clicked.connect(self.toggle_connection)
        connection_layout.addWidget(self.connect_button, 1, 3)
        
        # 添加查看路径按钮
        self.paths_button = QPushButton("查看路径")
        self.paths_button.clicked.connect(self.show_paths_info)
        connection_layout.addWidget(self.paths_button, 0, 4)
        
        connection_group.setLayout(connection_layout)
        main_layout.addWidget(connection_group)
        
        # 创建图表设置组
        chart_settings_group = QGroupBox("图表设置")
        chart_settings_layout = QGridLayout()
        
        # 添加图表类型选择
        chart_settings_layout.addWidget(QLabel("PRPD图类型:"), 0, 0)
        self.chart_type_combo = QComboBox()
        self.chart_type_combo.addItems(["散点图", "线图"])
        self.chart_type_combo.currentIndexChanged.connect(self.update_plot_type)
        chart_settings_layout.addWidget(self.chart_type_combo, 0, 1)
        
        # 添加数据缓冲区大小设置
        chart_settings_layout.addWidget(QLabel("数据缓冲区大小:"), 0, 2)
        self.buffer_size_spin = QSpinBox()
        self.buffer_size_spin.setRange(10, 1000)
        self.buffer_size_spin.setValue(self.max_buffer_size)
        self.buffer_size_spin.valueChanged.connect(self.update_buffer_size)
        chart_settings_layout.addWidget(self.buffer_size_spin, 0, 3)
        
        # 添加PRPD周期数设置
        chart_settings_layout.addWidget(QLabel("PRPD累积周期数:"), 1, 0)
        self.cycles_spin = QSpinBox()
        self.cycles_spin.setRange(1, 800)
        self.cycles_spin.setValue(self.max_cycles)
        self.cycles_spin.valueChanged.connect(self.update_max_cycles)
        chart_settings_layout.addWidget(self.cycles_spin, 1, 1)
        
        # 添加周期计数显示
        chart_settings_layout.addWidget(QLabel("当前周期:"), 1, 2)
        self.cycle_count_label = QLabel(f"{self.cycle_count}/{self.max_cycles}")
        chart_settings_layout.addWidget(self.cycle_count_label, 1, 3)
        
        # 添加显示参考正弦波选项
        self.show_sine_checkbox = QCheckBox("显示参考正弦波")
        self.show_sine_checkbox.setChecked(self.show_sine_wave)
        self.show_sine_checkbox.stateChanged.connect(self.toggle_sine_wave)
        chart_settings_layout.addWidget(self.show_sine_checkbox, 2, 0, 1, 1)
        
        # 添加正弦波振幅设置
        chart_settings_layout.addWidget(QLabel("正弦波振幅:"), 2, 1)
        self.sine_amplitude_spin = QDoubleSpinBox()
        self.sine_amplitude_spin.setRange(0.1, 3.0)
        self.sine_amplitude_spin.setValue(self.sine_amplitude)
        self.sine_amplitude_spin.setSingleStep(0.1)
        self.sine_amplitude_spin.valueChanged.connect(self.update_sine_params)
        chart_settings_layout.addWidget(self.sine_amplitude_spin, 2, 2)
        
        # 添加单位转换按钮
        self.unit_button = QPushButton("单位: mV")
        self.unit_button.clicked.connect(self.toggle_unit)
        chart_settings_layout.addWidget(self.unit_button, 2, 3)
        
        # 添加PRPS周期数说明
        chart_settings_layout.addWidget(QLabel("PRPS固定显示最新50个周期"), 3, 2, 1, 2)
        
        # 添加颜色方案选择
        chart_settings_layout.addWidget(QLabel("PRPS颜色方案:"), 4, 0)
        self.color_scheme_combo = QComboBox()
        self.color_scheme_combo.addItems(list(self.color_schemes.keys()))
        self.color_scheme_combo.setCurrentText(self.current_color_scheme)
        self.color_scheme_combo.currentTextChanged.connect(self.update_color_scheme)
        chart_settings_layout.addWidget(self.color_scheme_combo, 4, 1)
        
        # 添加数据库保存选项
        self.save_db_checkbox = QCheckBox("保存数据到数据库")
        self.save_db_checkbox.setChecked(self.save_to_db)
        self.save_db_checkbox.stateChanged.connect(self.toggle_db_save)
        chart_settings_layout.addWidget(self.save_db_checkbox, 4, 3)
        
        # 添加显示3D图选项
        self.show_3d_checkbox = QCheckBox("显示PRPS三维图")
        self.show_3d_checkbox.setChecked(self.show_3d_plot)
        self.show_3d_checkbox.stateChanged.connect(self.toggle_3d_plot)
        chart_settings_layout.addWidget(self.show_3d_checkbox, 3, 0, 1, 2)
        
        # 添加清除数据按钮
        self.clear_button = QPushButton("清除数据")
        self.clear_button.clicked.connect(self.clear_data)
        chart_settings_layout.addWidget(self.clear_button, 0, 4)
        
        # 添加重置周期按钮
        self.reset_cycles_button = QPushButton("重置周期")
        self.reset_cycles_button.clicked.connect(self.reset_cycles)
        chart_settings_layout.addWidget(self.reset_cycles_button, 1, 4)
        
        # 添加查看数据库按钮
        self.view_db_button = QPushButton("查看数据库")
        self.view_db_button.clicked.connect(self.show_database_view)
        chart_settings_layout.addWidget(self.view_db_button, 4, 4)
        
        # 添加保存CSV按钮
        self.save_csv_button = QPushButton("保存CSV")
        self.save_csv_button.clicked.connect(self.save_to_csv)
        chart_settings_layout.addWidget(self.save_csv_button, 3, 4)
        
        # 添加自动保存图像选项
        self.auto_save_checkbox = QCheckBox("自动保存PRPD图")
        self.auto_save_checkbox.setChecked(self.auto_save_images)
        self.auto_save_checkbox.stateChanged.connect(self.toggle_auto_save)
        chart_settings_layout.addWidget(self.auto_save_checkbox, 2, 4)
        
        chart_settings_group.setLayout(chart_settings_layout)
        main_layout.addWidget(chart_settings_group)
        
        # 创建matplotlib画布
        self.canvas = MplCanvas(self, width=10, height=4, dpi=100, with_3d=self.show_3d_plot, unit_label=self.unit_label)
        
        # 创建matplotlib工具栏
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # 添加画布和工具栏到布局中
        canvas_layout = QVBoxLayout()
        canvas_layout.addWidget(self.toolbar)
        canvas_layout.addWidget(self.canvas)
        
        canvas_widget = QWidget()
        canvas_widget.setLayout(canvas_layout)
        
        main_layout.addWidget(canvas_widget)
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 添加连接状态标签
        self.connection_status_label = QLabel("未连接")
        self.status_bar.addWidget(self.connection_status_label)
        
        # 添加数据点数量标签
        self.data_count_label = QLabel("数据点: 0")
        self.status_bar.addPermanentWidget(self.data_count_label)
    
    def toggle_3d_plot(self, state):
        """切换是否显示3D图"""
        self.show_3d_plot = (state == Qt.CheckState.Checked.value)
        
        # 重新创建画布
        old_canvas = self.canvas
        self.canvas = MplCanvas(self, width=10, height=4, dpi=100, with_3d=self.show_3d_plot, unit_label=self.unit_label)
        
        # 更新工具栏以使用新画布
        old_toolbar = self.toolbar
        self.toolbar = NavigationToolbar(self.canvas, self)
        
        # 获取包含画布和工具栏的布局
        canvas_layout = self.centralWidget().layout().itemAt(2).widget().layout()
        
        # 替换工具栏和画布
        canvas_layout.replaceWidget(old_toolbar, self.toolbar)
        canvas_layout.replaceWidget(old_canvas, self.canvas)
        
        old_toolbar.setParent(None)
        old_canvas.setParent(None)
        
        # 强制重绘
        self.need_redraw = True
    
    def toggle_connection(self):
        """切换MQTT连接状态"""
        if not self.mqtt_client.connected:
            # 连接到Broker
            self.connect_button.setEnabled(False)  # 禁用按钮，防止重复点击
            self.status_bar.showMessage("正在连接...", 2000)
            
            broker_address = self.broker_address_input.text()
            broker_port = self.broker_port_input.text()
            topic = self.topic_input.text()
            
            # 使用QTimer延迟执行连接操作，避免UI卡顿
            QTimer.singleShot(100, lambda: self._connect_mqtt(broker_address, broker_port, topic))
        else:
            # 断开连接
            self.connect_button.setEnabled(False)  # 禁用按钮，防止重复点击
            self.status_bar.showMessage("正在断开连接...", 2000)
            
            # 使用QTimer延迟执行断开连接操作，避免UI卡顿
            QTimer.singleShot(100, self._disconnect_mqtt)
    
    def _connect_mqtt(self, broker_address, broker_port, topic):
        """连接到MQTT Broker的实际操作"""
        try:
            if self.mqtt_client.connect_to_broker(broker_address, broker_port, topic):
                self.connect_button.setText("断开")
            else:
                self.status_bar.showMessage("连接失败", 3000)
        except Exception as e:
            self.status_bar.showMessage(f"连接时出错: {str(e)}", 3000)
        finally:
            self.connect_button.setEnabled(True)  # 重新启用按钮
    
    def _disconnect_mqtt(self):
        """断开MQTT连接的实际操作"""
        try:
            self.mqtt_client.disconnect_from_broker()
        except Exception as e:
            self.status_bar.showMessage(f"断开连接时出错: {str(e)}", 3000)
        finally:
            self.connect_button.setText("连接")
            self.connect_button.setEnabled(True)  # 重新启用按钮
    
    def update_connection_status(self, connected, message):
        """更新连接状态"""
        if connected:
            self.connection_status_label.setText(message)
            self.connection_status_label.setStyleSheet("color: green")
        else:
            self.connection_status_label.setText(message)
            self.connection_status_label.setStyleSheet("color: red")
            self.connect_button.setText("连接")
    
    def update_buffer_size(self, size):
        """更新数据缓冲区大小"""
        self.max_buffer_size = size
        self.data_mutex.lock()
        if len(self.data_buffer) > self.max_buffer_size:
            self.data_buffer = self.data_buffer[-self.max_buffer_size:]
            self.need_redraw = True
        self.data_mutex.unlock()
    
    def update_max_cycles(self, cycles):
        """更新最大周期数"""
        self.max_cycles = cycles
        self.cycle_count_label.setText(f"{self.cycle_count}/{self.max_cycles}")
        self.need_redraw = True
    
    def reset_cycles(self):
        """重置周期计数和累积数据"""
        self.data_mutex.lock()
        self.cycle_count = 1
        self.accumulated_data = []
        self.cycle_count_label.setText(f"{self.cycle_count}/{self.max_cycles}")
        self.need_redraw = True
        self.data_mutex.unlock()
        self.status_bar.showMessage("周期已重置", 2000)
    
    def update_plot_type(self):
        """更新图表类型"""
        self.need_redraw = True
    
    def clear_data(self):
        """清除数据"""
        self.data_mutex.lock()
        self.data_buffer = []
        self.accumulated_data = []
        self.cycle_count = 1
        self.cycle_count_label.setText(f"{self.cycle_count}/{self.max_cycles}")
        self.data_mutex.unlock()
        
        # 清除2D图
        self.canvas.axes_2d.clear()
        self.canvas.axes_2d.grid(True, linestyle='--', alpha=0.7)
        self.canvas.scatter = None
        self.canvas.line = None
        
        # 清除3D图
        if self.canvas.axes_3d:
            self.canvas.axes_3d.clear()
            self.canvas.axes_3d.set_title("PRPS图")
            self.canvas.axes_3d.set_xlabel("相位 °)")
            self.canvas.axes_3d.set_ylabel("周期")
            self.canvas.axes_3d.set_zlabel(self.unit_label)
            self.canvas.surface = None
        
        self.canvas.draw()
        self.data_count_label.setText("数据点: 0")
    
    def update_plot(self, data):
        """更新数据，但不立即重绘"""
        current_time = time.time()
        
        # 更新数据缓冲区
        self.data_mutex.lock()
        self.data_buffer = data
        
        # 处理周期数据
        # 每收到一次数据视为一个周期
        if len(data) > 0:
            # 添加新周期数据
            self.accumulated_data.append(data)
            
            # 如果累积的周期数超过PRPS的最大周期数，则移除最早的周期数据
            # 但保留足够的数据以满足PRPD图和PRPS图的需求
            max_needed_cycles = max(self.max_cycles, self.prps_max_cycles)
            if len(self.accumulated_data) > max_needed_cycles:
                self.accumulated_data = self.accumulated_data[-max_needed_cycles:]
            
            # 更新周期计数
            self.cycle_count = min(self.cycle_count + 1, self.max_cycles)
            self.cycle_count_label.setText(f"{self.cycle_count}/{self.max_cycles}")
            
            # 保存周期数据到数据库（确保在主线程中执行）
            if self.save_to_db and self.db_manager is not None:
                try:
                    self.db_manager.save_cycle_data(self.cycle_count, data)
                except Exception as e:
                    print(f"保存周期数据错误: {str(e)}")
        
        if len(self.data_buffer) > self.max_buffer_size:
            self.data_buffer = self.data_buffer[-self.max_buffer_size:]
        
        self.need_redraw = True
        self.data_mutex.unlock()
        
        # 更新数据点数量标签
        total_points = sum(len(cycle_data) for cycle_data in self.accumulated_data)
        self.data_count_label.setText(f"数据点: {total_points}")
    
    def redraw_plot(self):
        """重绘图表，由定时器触发"""
        if not self.need_redraw:
            return
            
        self.data_mutex.lock()
        accumulated_data_copy = self.accumulated_data.copy()
        self.data_mutex.unlock()
        
        if not accumulated_data_copy:
            return
        
        # 绘制2D图 (PRPD)
        self.draw_prpd(accumulated_data_copy)
        
        # 如果启用了3D图，则绘制PRPS图
        if self.show_3d_plot and self.canvas.axes_3d:
            self.draw_prps(accumulated_data_copy)
        
        # 重绘画布
        self.canvas.fig.tight_layout()
        self.canvas.draw()
        
        self.need_redraw = False
    
    def draw_prpd(self, accumulated_data):
        """绘制PRPD图"""
        # 清除当前2D图
        self.canvas.axes_2d.clear()
        
        # 根据选择的图表类型绘制
        chart_type = self.chart_type_combo.currentText()
        
        # 只使用PRPD需要的周期数
        prpd_data = accumulated_data[-self.max_cycles:] if len(accumulated_data) > self.max_cycles else accumulated_data
        
        # 合并所有周期的数据用于绘图
        all_data = []
        for cycle_data in prpd_data:
            all_data.extend(cycle_data)
        
        if not all_data:
            return
            
        # 创建X轴数据（相位）
        # 对于累积数据，我们需要为每个周期的每个数据点分配相位值
        phase_per_cycle = 360  # 每个周期的相位范围
        x_data = []
        
        for i, cycle_data in enumerate(prpd_data):
            cycle_phases = np.linspace(0, phase_per_cycle, len(cycle_data))
            x_data.extend(cycle_phases)
        
        # 根据当前单位设置转换数据
        if self.use_dbm:
            display_data = []
            for cycle_data in prpd_data:
                display_data.append([self.convert_unit(x, True) for x in cycle_data])
            
            # 合并所有周期的转换后数据
            all_display_data = []
            for cycle_data in display_data:
                all_display_data.extend(cycle_data)
        else:
            display_data = prpd_data
            all_display_data = all_data
        
        if chart_type == "散点图":
            self.canvas.axes_2d.scatter(x_data, all_display_data, alpha=0.7, s=10)
        elif chart_type == "线图":
            # 对于线图，我们可能需要按周期分别绘制
            for i, cycle_data in enumerate(display_data):
                cycle_phases = np.linspace(0, phase_per_cycle, len(cycle_data))
                self.canvas.axes_2d.plot(cycle_phases, cycle_data, linewidth=1.0, 
                                     label=f"周期 {i+1}")
            # 如果周期数较多，可以选择不显示图例
            if len(display_data) <= 3:
                self.canvas.axes_2d.legend(loc='upper right')
        
        # 绘制参考正弦波
        if self.show_sine_wave:
            # 确定数据的振幅范围，用于缩放正弦波
            if all_display_data:
                max_data = max(all_display_data)
                min_data = min(all_display_data)
                data_range = max_data - min_data
                # 计算正弦波的振幅，使其与数据的振幅范围相适应
                sine_amp = self.sine_amplitude * data_range / 4
                # 计算正弦波的偏移量，使其居中显示
                sine_offset = (max_data + min_data) / 2
            else:
                sine_amp = self.sine_amplitude
                sine_offset = 0
            
            # 生成正弦波数据
            x_sine = np.linspace(0, phase_per_cycle, 1000)
            y_sine = sine_amp * np.sin(x_sine * 2 * np.pi / phase_per_cycle) + sine_offset
            
            # 绘制正弦波
            self.canvas.axes_2d.plot(x_sine, y_sine, 'r-', linewidth=1.5, alpha=0.7, label="参考正弦波")
        
        # 设置图表标题和轴标签
        cycle_info = f"({len(prpd_data)}/{self.max_cycles}周期)"
        self.canvas.axes_2d.set_title(f"PRPD图 {cycle_info}")
        self.canvas.axes_2d.set_xlabel("相位°)")
        self.canvas.axes_2d.set_ylabel(self.unit_label)
        
        # 设置网格
        self.canvas.axes_2d.grid(True, linestyle='--', alpha=0.7)
    
    def draw_prps(self, accumulated_data):
        """绘制PRPS三维图"""
        # 清除当前3D图并重新创建
        self.canvas.fig.delaxes(self.canvas.axes_3d)
        self.canvas.axes_3d = self.canvas.fig.add_subplot(122, projection='3d')
        
        # 移除之前的颜色条
        try:
            if hasattr(self.canvas, 'colorbar'):
                # 尝试安全地移除颜色条
                self.canvas.colorbar.remove()
                delattr(self.canvas, 'colorbar')
        except Exception:
            # 如果移除失败，直接忽略
            pass
        
        # 只使用PRPS需要的最新周期数
        prps_data = accumulated_data[-self.prps_max_cycles:] if len(accumulated_data) > self.prps_max_cycles else accumulated_data
        
        # 准备数据
        num_cycles = len(prps_data)
        if num_cycles == 0:
            return
            
        # 找到所有周期中最大的数据点数
        max_points = max(len(cycle_data) for cycle_data in prps_data)
        
        # 创建规则网格
        phase = np.linspace(0, 360, max_points)
        cycles = np.arange(1, num_cycles + 1)
        
        # 创建空的Z值矩阵
        z_data = np.zeros((num_cycles, max_points))
        
        # 填充Z值矩阵
        for i, cycle_data in enumerate(prps_data):
            # 对于每个周期，我们需要将数据重采样到max_points个点
            if len(cycle_data) == max_points:
                z_data[i, :] = cycle_data
            else:
                # 如果周期的数据点数不等于max_points，则需要重采样
                cycle_phases = np.linspace(0, 360, len(cycle_data))
                z_data[i, :] = np.interp(phase, cycle_phases, cycle_data)
        
        # 根据当前单位设置转换数据
        if self.use_dbm:
            # 转换z_data中的每个值
            for i in range(z_data.shape[0]):
                for j in range(z_data.shape[1]):
                    z_data[i, j] = self.convert_unit(z_data[i, j], True)
        
        # 创建网格
        X, Y = np.meshgrid(phase, cycles)
        
        # 创建自定义颜色映射
        custom_cmap = self.create_custom_colormap(self.color_schemes[self.current_color_scheme])
        
        # 绘制3D表面
        surf = self.canvas.axes_3d.plot_surface(X, Y, z_data, cmap=custom_cmap, 
                                           edgecolor='none', alpha=0.8)
        
        # 添加颜色条，并将其保存为实例属性
        self.canvas.colorbar = self.canvas.fig.colorbar(surf, ax=self.canvas.axes_3d, shrink=0.5, aspect=5)
        
        # 设置图表标题和轴标签
        self.canvas.axes_3d.set_title(f"PRPS图 ({num_cycles}个周期)")
        self.canvas.axes_3d.set_xlabel("相位")
        self.canvas.axes_3d.set_ylabel("周期")
        self.canvas.axes_3d.set_zlabel(self.unit_label)
        
        # 强制设置坐标轴范围和刻度
        self.canvas.axes_3d.set_xlim(0, 360)  # 相位范围固定为0-360度
        self.canvas.axes_3d.set_ylim(1, num_cycles)  # 周期范围
        
        # 设置Z轴范围（根据数据动态调整，但保持一定的稳定性）
        z_min = np.min(z_data) - 0.1 * (np.max(z_data) - np.min(z_data))  # 确保有足够的下边界空间
        z_max = np.max(z_data) + 0.1 * (np.max(z_data) - np.min(z_data))  # 确保有足够的上边界空间
        
        # 针对dBm单位进行特殊处理
        if self.use_dbm:
            # 对于dBm单位，我们可能需要更宽的范围
            # 确保最小值不会太小，避免显示大量无意义的空白区域
            if z_min < -80:
                z_min = -80  # dBm的一个合理下限
            
            # 确保范围足够宽以显示有意义的数据
            if z_max - z_min < 20:
                z_mean = (z_max + z_min) / 2
                z_min = z_mean - 10
                z_max = z_mean + 10
        else:
            # 对于毫伏单位，确保最小值不低于0（物理上有意义）
            if z_min < 0:
                z_min = 0
        
        self.canvas.axes_3d.set_zlim(z_min, z_max)
        
        # 设置视角和投影方式
        # self.canvas.axes_3d.view_init(elev=30, azim=270)
        self.canvas.axes_3d.set_box_aspect((1.5, 1, 0.8))  # 固定图形纵横比
    
    def update_status(self):
        """更新状态信息"""
        # 更新数据库状态
        if self.db_manager is not None and self.db_manager.connected:
            cycle_count = self.db_manager.get_cycle_count()
            raw_count = self.db_manager.get_raw_count()
            db_status = f"数据库: 已连接 (周期数据: {cycle_count}, 原始数据: {raw_count})"
            
            # 检查是否正在保存数据
            if self.save_to_db:
                db_status += " [数据保存已启用]"
            else:
                db_status += " [数据保存已禁用]"
                
            # 更新状态栏
            if hasattr(self, 'db_status_label'):
                self.db_status_label.setText(db_status)
            else:
                self.db_status_label = QLabel(db_status)
                self.status_bar.addPermanentWidget(self.db_status_label)
    
    def closeEvent(self, event):
        """关闭窗口事件"""
        # 断开MQTT连接
        self.mqtt_client.disconnect_from_broker()
        
        # 关闭数据库连接
        if self.db_manager is not None:
            self.db_manager.close()
            
        event.accept()

    def update_color_scheme(self, scheme_name):
        """更新PRPS图的颜色方案"""
        self.current_color_scheme = scheme_name
        # 强制重绘
        self.need_redraw = True

    def toggle_sine_wave(self, state):
        """切换是否显示参考正弦波"""
        self.show_sine_wave = (state == Qt.CheckState.Checked.value)
        self.need_redraw = True

    def update_sine_params(self, amplitude):
        """更新参考正弦波的振幅"""
        self.sine_amplitude = amplitude
        self.need_redraw = True

    def toggle_db_save(self, state):
        """切换是否保存数据到数据库"""
        self.save_to_db = (state == Qt.CheckState.Checked.value)
        self.need_redraw = True

    def save_raw_data(self, broker, topic, raw_data):
        """保存原始数据到数据库（在主线程中执行）"""
        if self.save_to_db and self.db_manager is not None:
            try:
                self.db_manager.save_raw_data(broker, topic, raw_data)
            except Exception as e:
                print(f"保存原始数据错误（主线程）: {str(e)}")

    def show_database_view(self):
        """显示数据库查看对话框"""
        if self.db_manager is not None and self.db_manager.connected:
            dialog = DatabaseViewDialog(self.db_manager, self)
            dialog.exec()
        else:
            QMessageBox.warning(self, "数据库未连接", "数据库未连接或连接失败，无法查看数据。")

    def toggle_unit(self):
        """切换单位显示（毫伏mV和dBm）"""
        self.use_dbm = not self.use_dbm
        
        if self.use_dbm:
            self.unit_button.setText("单位: dBm")
            self.unit_label = "幅值 (dBm)"
        else:
            self.unit_button.setText("单位: mV")
            self.unit_label = "幅值 (mV)"
        
        # 强制重绘
        self.need_redraw = True
    
    def convert_unit(self, value, to_dbm=True):
        """转换单位
        
        Args:
            value: 要转换的值
            to_dbm: 如果为True，将毫伏转换为dBm；如果为False，将dBm转换为毫伏
            
        Returns:
            转换后的值
        """
        if to_dbm:
            # 毫伏转dBm: 毫伏值*54.545-81.818
            return value * 54.545 - 81.818
        else:
            # dBm转毫伏: (dBm值+81.818)/54.545
            return (value + 81.818) / 54.545
    
    def convert_data_for_display(self, data):
        """根据当前单位设置转换数据用于显示
        
        Args:
            data: 原始数据（毫伏值）
            
        Returns:
            转换后的数据
        """
        if self.use_dbm:
            if isinstance(data, list):
                return [self.convert_unit(x, True) for x in data]
            elif isinstance(data, np.ndarray):
                return np.array([self.convert_unit(x, True) for x in data.flatten()]).reshape(data.shape)
            else:
                return self.convert_unit(data, True)
        else:
            return data  # 如果使用毫伏，则不需要转换

    def save_to_csv(self):
        """保存周期数据到CSV文件"""
        # 检查是否有足够的数据
        self.data_mutex.lock()
        if not self.accumulated_data:
            self.data_mutex.unlock()
            QMessageBox.warning(self, "无数据", "没有可用的周期数据可保存。")
            return
        
        # 复制数据，避免在保存过程中数据被修改
        data_to_save = self.accumulated_data.copy()
        self.data_mutex.unlock()
        
        # 生成默认文件名（年月日时分秒.csv）
        default_filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S.csv")
        
        # 获取保存路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存CSV数据", default_filename, "CSV文件 (*.csv);;所有文件 (*.*)"
        )
        
        if not file_path:
            return  # 用户取消了保存操作
        
        try:
            # 只保存最新的50个周期（或者全部如果少于50个）
            cycles_to_save = min(self.csv_export_cycles, len(data_to_save))
            csv_data = data_to_save[-cycles_to_save:]
            
            # 打开CSV文件进行写入
            with open(file_path, 'w', newline='') as csvfile:
                csv_writer = csv.writer(csvfile)
                
                # 直接写入数据，不包含表头和周期编号
                for cycle_data in csv_data:
                    csv_writer.writerow(cycle_data)
            
            QMessageBox.information(self, "保存成功", f"已成功保存{cycles_to_save}个周期的数据到:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "保存失败", f"保存CSV文件时发生错误:\n{str(e)}")

    def toggle_auto_save(self, state):
        """切换是否自动保存图像"""
        self.auto_save_images = (state == Qt.CheckState.Checked.value)
        
        if self.auto_save_images:
            # 启动自动保存定时器
            self.image_save_timer.start(self.image_save_interval)
            self.status_bar.showMessage("已启用自动保存PRPD图，每5秒保存一次", 3000)
        else:
            # 停止自动保存定时器
            self.image_save_timer.stop()
            self.status_bar.showMessage("已禁用自动保存PRPD图", 3000)
    
    def auto_save_image(self):
        """自动保存PRPD图像"""
        if not self.auto_save_images or not self.accumulated_data:
            return
        
        try:
            # 使用已经在get_save_paths中计算好的图像保存路径
            save_dir = self.images_path
            
            # 确保保存目录存在
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            
            # 生成文件名
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            filename = f"PRPD_{timestamp}.png"
            file_path = os.path.join(save_dir, filename)
            
            # 保存当前PRPD图像
            # 创建一个新的Figure以确保只保存PRPD图（不包含PRPS图）
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            # 复制当前PRPD图的内容
            chart_type = self.chart_type_combo.currentText()
            
            # 获取当前数据
            self.data_mutex.lock()
            prpd_data = self.accumulated_data[-self.max_cycles:] if len(self.accumulated_data) > self.max_cycles else self.accumulated_data.copy()
            self.data_mutex.unlock()
            
            # 合并所有周期的数据用于绘图
            all_data = []
            x_data = []
            
            for cycle_data in prpd_data:
                all_data.extend(cycle_data)
                cycle_phases = np.linspace(0, 360, len(cycle_data))
                x_data.extend(cycle_phases)
            
            # 根据当前单位设置转换数据
            if self.use_dbm:
                display_data = []
                for cycle_data in prpd_data:
                    display_data.append([self.convert_unit(x, True) for x in cycle_data])
                
                # 合并所有周期的转换后数据
                all_display_data = []
                for cycle_data in display_data:
                    all_display_data.extend(cycle_data)
            else:
                display_data = prpd_data
                all_display_data = all_data
            
            if chart_type == "散点图":
                ax.scatter(x_data, all_display_data, alpha=0.7, s=10)
            elif chart_type == "线图":
                # 对于线图，按周期分别绘制
                for i, cycle_data in enumerate(display_data):
                    cycle_phases = np.linspace(0, 360, len(cycle_data))
                    ax.plot(cycle_phases, cycle_data, linewidth=1.0)
            
            # 绘制参考正弦波
            if self.show_sine_wave:
                # 确定数据的振幅范围，用于缩放正弦波
                if all_display_data:
                    max_data = max(all_display_data)
                    min_data = min(all_display_data)
                    data_range = max_data - min_data
                    # 计算正弦波的振幅，使其与数据的振幅范围相适应
                    sine_amp = self.sine_amplitude * data_range / 4
                    # 计算正弦波的偏移量，使其居中显示
                    sine_offset = (max_data + min_data) / 2
                else:
                    sine_amp = self.sine_amplitude
                    sine_offset = 0
                
                # 生成正弦波数据
                x_sine = np.linspace(0, 360, 1000)
                y_sine = sine_amp * np.sin(x_sine * 2 * np.pi / 360) + sine_offset
                
                # 绘制正弦波
                ax.plot(x_sine, y_sine, 'r-', linewidth=1.5, alpha=0.7, label="参考正弦波")
            
            # 设置图表标题和轴标签
            cycle_info = f"({len(prpd_data)}/{self.max_cycles}周期)"
            ax.set_title(f"PRPD图 {cycle_info}")
            ax.set_xlabel("相位")
            ax.set_ylabel(self.unit_label)
            
            # 设置网格
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # 保存图像
            fig.tight_layout()
            fig.savefig(file_path)
            
            # 更新状态栏
            self.status_bar.showMessage(f"已保存PRPD图: {filename}", 3000)
            
        except Exception as e:
            print(f"保存PRPD图像错误: {str(e)}")
            self.status_bar.showMessage(f"保存PRPD图像失败: {str(e)}", 3000)

    def create_custom_colormap(self, colors):
        """
        根据给定的颜色列表创建自定义颜色映射
        
        :param colors: 颜色列表，至少包含4种颜色
        :return: matplotlib颜色映射对象
        """
        import matplotlib.colors as mcolors
        import matplotlib.pyplot as plt
        
        # 确保有足够的颜色
        if len(colors) < 4:
            colors = colors + ['#FF0000']  # 默认添加红色
        
        # 创建颜色映射
        n_bins = 100  # 颜色渐变的细腻程度
        cmap = mcolors.LinearSegmentedColormap.from_list(
            'custom_colormap', 
            [mcolors.to_rgba(color) for color in colors[:4]], 
            N=n_bins
        )
        
        return cmap

    def get_save_paths(self):
        """获取数据库和图像保存路径"""
        try:
            # 获取应用程序路径
            if getattr(sys, 'frozen', False):
                # 如果是打包后的应用程序，使用可执行文件所在目录
                # 注意：不使用sys._MEIPASS，因为那是临时目录，应用关闭后会被删除
                application_path = os.path.dirname(sys.executable)
            else:
                # 如果是普通Python脚本，使用脚本所在目录
                application_path = os.path.dirname(os.path.abspath(__file__))
        except Exception as e:
            # 如果出错，回退到当前工作目录
            application_path = os.getcwd()
            print(f"获取应用路径出错，使用当前工作目录: {application_path}, 错误: {str(e)}")
        
        # 保存路径信息
        self.db_path = os.path.join(application_path, "gis_pd_data.db")
        self.images_path = os.path.join(application_path, "saved_images")
        
        print(f"数据库路径: {self.db_path}")
        print(f"图像保存路径: {self.images_path}")
        
        # 创建图像保存目录（如果不存在）
        if not os.path.exists(self.images_path):
            try:
                os.makedirs(self.images_path)
                print(f"已创建图像保存目录: {self.images_path}")
            except Exception as e:
                print(f"创建图像保存目录失败: {str(e)}")
    
    def show_paths_info(self):
        """显示路径信息对话框"""
        info_text = f"数据库文件路径:\n{self.db_path}\n\n图像保存路径:\n{self.images_path}"
        QMessageBox.information(self, "文件保存路径信息", info_text)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 