# 北京-巴黎航班查询系统

## 项目简介

一个基于Flask的航班查询网站，用于查询北京到巴黎的航班信息、票价，并展示价格趋势。

## 技术栈

- Python 3.x
- Flask
- SQLite
- Chart.js (前端图表)

## 环境要求

- Python 3.8+
- Windows 10/11

---

## Windows 部署指南

### 方式一：开发模式运行（推荐开发测试）

```powershell
cd C:\Users\fli\Documents\Repositories\my_test_repo\flight_project
pip install -r requirements.txt
python run.py
```

访问 http://localhost:5000

---

### 方式二：生产环境运行（Gunicorn）

#### 1. 安装依赖和Gunicorn

```powershell
pip install -r requirements.txt
pip install gunicorn
```

#### 2. 启动服务

```powershell
cd C:\Users\fli\Documents\Repositories\my_test_repo\flight_project
gunicorn -w 4 -b 0.0.0.0:5000 "run:app"
```

- `-w 4`: 4个工作进程
- `-b 0.0.0.0:5000`: 监听地址和端口

访问 http://localhost:5000

#### 3. 后台运行（带日志）

```powershell
gunicorn -w 4 -b 0.0.0.0:5000 --access-logfile access.log --error-logfile error.log --daemon "run:app"
```

#### 4. 停止服务

```powershell
taskkill /F /IM gunicorn.exe
```

---

### 方式三：使用批处理脚本（推荐）

创建启动脚本 `start.bat`：

```batch
@echo off
cd /d "%~dp0flight_project"
echo Starting Flight Search Server...
gunicorn -w 4 -b 0.0.0.0:5000 --daemon "run:app"
echo Server started on http://localhost:5000
timeout /t 2 >nul
```

创建停止脚本 `stop.bat`：

```batch
@echo off
echo Stopping Gunicorn...
taskkill /F /IM gunicorn.exe 2>nul
echo Server stopped
pause
```

双击 `start.bat` 启动，双击 `stop.bat` 停止。

---

### SQLite 数据库

数据库文件 `flights.db` 会在首次运行时自动创建在 `flight_project` 目录下。

---

## 功能特性

- 查询北京(PEK)到巴黎(CDG/ORY)的航班
- 支持直飞/单程转机/双程转机
- 筛选条件：出发日期、返回日期、人数、舱位等级
- 航班列表展示：航空公司、起降时间、价格、剩余座位
- 价格趋势图（时间序列）
- 后台SQLite数据库存储

## 数据库表

- `airlines`: 航空公司信息
- `flights`: 航班信息
- `flight_prices`: 票价历史
- `search_history`: 查询历史
