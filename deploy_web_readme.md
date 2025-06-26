# GIS局部放电在线监测系统 - Web版部署指南

## 系统概述

GIS局部放电在线监测系统Web版是一个基于FastAPI框架开发的实时监测系统，用于显示GIS设备的局部放电数据，包括PRPD（相位分辨局部放电）和PRPS（相位分辨脉冲序列）图表。系统从SQLite数据库读取数据，通过WebSocket实现实时数据传输和可视化。

## 系统要求

- Python 3.8+
- 支持现代浏览器（Chrome、Firefox、Edge等）
- SQLite数据库

## 部署步骤

### 1. 准备环境

首先，确保您的系统已安装Python 3.8或更高版本：

```bash
python --version
```

### 2. 获取代码

将项目代码克隆或下载到您的服务器：

```bash
git clone <项目仓库地址>
# 或者直接下载ZIP文件并解压
```

### 3. 创建虚拟环境（推荐）

在项目根目录下创建并激活Python虚拟环境：

```bash
# 创建虚拟环境
python -m venv venv

# 在Windows上激活虚拟环境
venv\Scripts\activate

# 在Linux/Mac上激活虚拟环境
source venv/bin/activate
```

### 4. 安装依赖

安装项目所需的所有依赖包：

```bash
pip install -r requirements.txt
```

### 5. 配置数据库

系统默认使用项目根目录下的`gis_pd_data.db`作为数据库文件。如果您需要使用现有数据库，请确保将其放置在正确位置。

如果需要创建新的数据库，系统会在首次运行时自动创建所需的表结构。

### 6. 启动Web服务

在项目的`gis_pd_web`目录下运行以下命令启动Web服务：

```bash
cd gis_pd_web
python run.py
```

默认情况下，服务将在`http://127.0.0.1:8000`上运行。如需修改端口或主机设置，请编辑`run.py`文件中的相关参数。

### 7. 访问Web界面

打开浏览器，访问：

```
http://127.0.0.1:8000
```

您应该能看到GIS局部放电监测系统的Web界面。

## 系统配置

### 数据库配置

数据库连接参数位于`gis_pd_web/db_utils.py`文件中，默认使用项目根目录下的`gis_pd_data.db`文件。如需修改数据库路径，请更新该文件中的`DATABASE_URL`变量。

### WebSocket配置

WebSocket连接参数位于前端JavaScript文件中，默认连接到与Web服务相同的主机和端口。如果您在不同的主机或端口上部署WebSocket服务，请相应地更新前端代码。

## 功能特性

- **实时数据监测**：通过WebSocket实时显示最新的局部放电数据
- **PRPD图表**：显示相位分辨局部放电图，支持散点图和线图两种模式
- **PRPS三维图**：显示相位分辨脉冲序列三维图，固定显示最新的50个周期数据
- **历史数据查询**：支持按时间范围查询历史数据并生成图表
- **数据导出**：支持将数据导出为CSV格式
- **响应式设计**：适配不同尺寸的屏幕和设备

## 常见问题

### 1. 数据未显示或更新

- 检查数据库连接是否正常
- 确认数据库中是否有数据
- 检查WebSocket连接状态
- 尝试刷新浏览器页面

### 2. 图表显示异常

- 确保浏览器支持WebSocket和现代JavaScript特性
- 尝试清除浏览器缓存
- 检查浏览器控制台是否有错误信息

### 3. 服务无法启动

- 检查端口是否被占用
- 确认所有依赖包已正确安装
- 检查Python版本是否满足要求

## 进阶配置

### 部署到生产环境

对于生产环境，建议使用Nginx或Apache作为反向代理，并配合Gunicorn或Uvicorn作为ASGI服务器：

```bash
# 安装Gunicorn
pip install gunicorn

# 启动服务
cd gis_pd_web
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### Nginx配置示例

```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
}
```

## 系统更新

定期检查项目仓库以获取最新更新和功能改进。更新系统时，建议先备份数据库文件和任何自定义配置。

## 最近更新

**2025年6月**：Web版进行了多项优化和修复：
- 历史数据页面布局优化：PRPD和PRPS图表改为左右显示
- 修复历史PRPS三维图显示问题
- PRPS图表优化：始终显示最新的50个周期数据，Y轴设置为50，每条数据库记录对应一个周期

## 联系与支持

如有任何问题或需要技术支持，请联系系统管理员或开发团队。 