# 北京-巴黎航班查询系统

## 项目简介

一个基于Flask的航班查询网站，用于查询北京到巴黎的航班信息、票价，并展示价格趋势。

## 技术栈

- Python 3.x
- Flask
- SQLite
- Chart.js (前端图表)
- SerpAPI (可选，Google Flights 实时数据)

## 环境要求

- Python 3.8+
- Windows 10/11

---

## Windows 部署指南

### 方式一：开发模式运行

```powershell
cd C:\Users\fli\Documents\Repositories\my_test_repo\flight_project
pip install -r requirements.txt
python run.py
```

访问 http://localhost:5000

---

### 方式二：使用批处理脚本（推荐）

双击 `start.bat` 启动，双击 `stop.bat` 停止。

---

### SQLite 数据库

数据库文件 `flights.db` 会在首次运行时自动创建。

---

## SerpAPI 集成（可选）

### 1. 注册 SerpAPI

访问 https://serpapi.com/signup 获取免费 API Key（每月 100 次免费搜索）

### 2. 配置环境变量

设置以下环境变量启用 SerpAPI：

```powershell
# 启用 SerpAPI
set USE_SERPAPI=true
set SERPAPI_API_KEY=你的API密钥
```

或创建 `.env` 文件：

```
USE_SERPAPI=true
SERPAPI_API_KEY=你的API密钥
```

### 3. 数据源说明

- **默认**: 使用模拟数据（免费）
- **启用 SerpAPI**: 使用 Google Flights 实时数据

API 调用示例参数：
- `departure_id`: 出发机场 IATA 代码（如 PEK）
- `arrival_id`: 到达机场 IATA 代码（如 CDG）
- `outbound_date`: 出发日期（YYYY-MM-DD）
- `return_date`: 返回日期（YYYY-MM-DD）
- `currency`: 货币代码（CNY/USD/EUR）

---

## 功能特性

- 查询北京(PEK)到巴黎(CDG/ORY)的航班
- 支持直飞/单程转机/双程转机
- 筛选条件：出发日期、返回日期、人数、舱位等级
- 航班列表展示：航空公司、起降时间、价格、剩余座位
- 价格趋势图（时间序列）
- 后台SQLite数据库存储
- SerpAPI 集成实时价格查询

## 数据库表

- `airlines`: 航空公司信息
- `flights`: 航班信息
- `flight_prices`: 票价历史
- `search_history`: 查询历史
