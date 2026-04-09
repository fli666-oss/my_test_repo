# Beijing-Paris Flight Search System

## Project Overview

A Flask-based flight search website for querying flights from Beijing to Paris, displaying fares and price trends.

## Tech Stack

- Python 3.x
- Flask
- SQLite
- Chart.js

## Quick Start

### 1. Install Dependencies

```bash
cd flight_project
pip install -r requirements.txt
```

### 2. Create Database

```bash
cd flight_project
python -c "from run import app; from app.routes.main import init_db; app.app_context().push(); init_db()"
```

Or simply run:
```bash
python run.py
```

Database file `flights.db` will be created in `flight_project` directory.

### 3. Start Server

```bash
python run.py
```

Then access http://localhost:5000

## Features

- Search flights from Beijing (PEK) to Paris (CDG/ORY)
- Direct flights / one-stop / two-stop connections
- Filters: departure date, return date, passengers, cabin class
- Flight list: airline, departure/arrival time, price, available seats
- Price trend chart (time series)
- SQLite database storage

## Database Tables

- `airlines`: Airline information
- `flights`: Flight details
- `flight_prices`: Price history
- `search_history`: Search history
