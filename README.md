# GIS局部放电在线监测系统

## 项目概述

本项目是GIS（气体绝缘开关柜）局部放电在线监测系统，包含两个版本：

1. **桌面版** (gis_pd_mqtt_gui.py)：基于Python和PySide6开发的桌面应用程序
2. **Web版** (gis_pd_web目录)：基于Python FastAPI框架开发的Web应用程序

两个版本共用同一个SQLite数据库(gis_pd_data.db)，实现数据共享和统一管理。

## 项目结构

```
gis_pd_db/
  - gis_pd_data.db          # SQLite数据库文件
  - gis_pd_mqtt_gui.py      # 桌面版应用程序
  - gis_pd_web/             # Web版应用程序
    - db_utils.py           # 数据库工具类
    - main.py               # FastAPI主程序
    - README.md             # Web版详细说明
    - requirements.txt      # Web版依赖库
    - run.py                # Web版启动脚本
    - static/               # 静态资源
      - css/
        - style.css
      - images/
      - js/
        - main.js
    - templates/            # HTML模板
      - index.html
  - README.md               # 项目总体说明
  - requirements.txt        # 桌面版依赖库
```

## 功能特点

### 共同特点

- PRPD（相位分辨局部放电）图表显示
- PRPS（相位分辨脉冲序列）三维图表显示
- 数据库存储和管理
- 历史数据查询与分析

### 桌面版特点

- 基于PySide6的GUI界面
- MQTT客户端实时接收传感器数据
- 本地数据处理与可视化
- 详见：gis_pd_mqtt_gui.py

### Web版特点

- 基于FastAPI的Web服务
- WebSocket实时数据推送
- 浏览器端数据可视化
- 详见：[Web版详细说明](gis_pd_web/README.md)

## 安装与运行

### 桌面版

1. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

2. 运行桌面应用：
   ```
   python gis_pd_mqtt_gui.py
   ```

### Web版

1. 安装依赖：
   ```
   pip install -r gis_pd_web/requirements.txt
   ```

2. 运行Web应用：
   ```
   python gis_pd_web/run.py
   ```

3. 在浏览器中访问：http://localhost:8000

## 数据流程

1. **数据采集与存储**：桌面版应用通过MQTT接收传感器数据并存储到SQLite数据库
2. **数据读取与推送**：Web版应用从同一数据库读取数据并通过WebSocket推送到前端
3. **实时数据更新**：Web版不直接连接传感器，而是通过定期检查数据库中的新数据来实现"伪实时"更新
4. **数据可视化**：两个版本都提供PRPD和PRPS图表，但使用不同的可视化技术（桌面版使用Matplotlib，Web版使用Chart.js和Plotly.js）
5. **独立运行或协同工作**：两个版本可以独立运行，也可以同时运行，共享同一数据源

## 版权与许可

© 2023 GIS局部放电在线监测系统 