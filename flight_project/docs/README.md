# 北京-巴黎航班查询系统

## 项目简介

一个基于Flask的航班查询网站，用于查询北京到巴黎的航班信息、票价，并展示价格趋势。

## 技术栈

- Python 3.x
- Flask
- SQLite
- Chart.js (前端图表)

## 快速开始

### 1. 安装依赖

```bash
cd flight_project
pip install -r requirements.txt
```

### 2. 创建数据库

```bash
cd flight_project
python -c "from run import app; from app.routes.main import init_db; app.app_context().push(); init_db()"
```

或者直接运行：
```bash
python run.py
```

数据库文件 `flights.db` 会自动创建在 `flight_project` 目录下。

### 3. 启动服务

```bash
python run.py
```

服务启动后访问 http://localhost:5000

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
