# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify
from datetime import datetime, date, timedelta
import os
import random

main_bp = Blueprint('main', __name__)

USE_SERPAPI = os.environ.get('USE_SERPAPI', 'false').lower() == 'true'
SERPAPI_API_KEY = os.environ.get('SERPAPI_API_KEY', '')

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/search', methods=['POST'])
def search_flights():
    from app.models.models import db, SearchHistory, FlightPrice
    data = request.get_json()
    
    origin = data.get('origin', 'PEK')
    destination = data.get('destination', 'CDG')
    departure_date = data.get('departure_date')
    return_date = data.get('return_date')
    passengers = int(data.get('passengers', 1))
    cabin_class = data.get('cabin_class', 'economy')
    
    if departure_date:
        departure_date_obj = datetime.strptime(departure_date, '%Y-%m-%d').date()
    else:
        return jsonify({'error': 'Missing departure_date'}), 400
    
    if return_date:
        return_date_obj = datetime.strptime(return_date, '%Y-%m-%d').date()
    else:
        return_date_obj = (departure_date_obj + timedelta(days=14))
        return_date = return_date_obj.isoformat()
    
    search = SearchHistory(
        origin=origin,
        destination=destination,
        departure_date=departure_date_obj,
        return_date=return_date_obj,
        passengers=passengers,
        cabin_class=cabin_class
    )
    db.session.add(search)
    db.session.commit()
    
    if USE_SERPAPI and SERPAPI_API_KEY:
        flights = search_flights_serpapi(origin, destination, departure_date, return_date, cabin_class, passengers)
    else:
        flights = search_flights_mock(origin, destination, departure_date_obj, cabin_class)
    
    for flight in flights:
        price_record = FlightPrice(
            flight_id=flight.get('id'),
            departure_date=departure_date_obj,
            cabin_class=cabin_class,
            price=flight.get('price', 0),
            currency='EUR',
            available_seats=flight.get('seats_available')
        )
        db.session.add(price_record)
    db.session.commit()
    
    return jsonify({
        'flights': flights,
        'search_info': {
            'origin': origin,
            'destination': destination,
            'departure_date': departure_date,
            'return_date': return_date,
            'passengers': passengers,
            'cabin_class': cabin_class
        },
        'data_source': 'serpapi' if USE_SERPAPI and SERPAPI_API_KEY else 'mock'
    })

@main_bp.route('/price-history')
def price_history():
    from app.models.models import db, FlightPrice
    origin = request.args.get('origin', 'PEK')
    destination = request.args.get('destination', 'CDG')
    departure_date = request.args.get('departure_date')
    cabin_class = request.args.get('cabin_class', 'economy')
    
    if departure_date:
        departure_date = datetime.strptime(departure_date, '%Y-%m-%d').date()
    else:
        departure_date = date.today() + timedelta(days=30)
    
    price_records = FlightPrice.query.filter(
        FlightPrice.departure_date == departure_date,
        FlightPrice.cabin_class == cabin_class
    ).order_by(FlightPrice.search_date.desc()).limit(60).all()
    
    if price_records:
        from collections import defaultdict
        by_date = defaultdict(list)
        for record in price_records:
            by_date[record.departure_date].append(record.price)
        
        history = []
        for d, prices in sorted(by_date.items()):
            avg_price = sum(prices) / len(prices)
            history.append({
                'date': d.isoformat(),
                'price': int(avg_price),
                'min_price': min(prices),
                'max_price': max(prices),
                'sample_count': len(prices)
            })
        return jsonify(history)
    
    price_history = generate_price_history(origin, destination, departure_date)
    return jsonify(price_history)

@main_bp.route('/airlines')
def get_airlines():
    from app.models.models import db, Airline
    airlines = Airline.query.all()
    return jsonify([{'code': a.code, 'name': a.name, 'name_cn': a.name_cn} for a in airlines])

def search_flights_serpapi(origin, destination, outbound_date, return_date, cabin_class, passengers=1):
    try:
        from serpapi import GoogleSearch
        
        travel_class_map = {
            'economy': 'ECONOMY',
            'business': 'BUSINESS',
            'first': 'FIRST'
        }
        
        params = {
            "api_key": SERPAPI_API_KEY,
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "outbound_date": outbound_date,
            "return_date": return_date,
            "currency": "EUR",
            "travel_class": travel_class_map.get(cabin_class, 'ECONOMY'),
            "adults": passengers,
            "trip_type": "ROUND_TRIP"
        }
        
        search = GoogleSearch(params)
        results = search.get_dict()
        
        flights = []
        best_flights = results.get('best_flights', [])
        other_flights = results.get('other_flights', [])
        
        all_flights = best_flights + other_flights
        
        for i, flight in enumerate(all_flights):
            flight_details = flight.get('flights', [])
            total_duration = flight.get('total_duration', 0)
            price = flight.get('price', 0)
            
            if not price:
                continue
            
            airline_info = flight_details[0] if flight_details else {}
            airline_name = airline_info.get('airline', 'Unknown')
            
            dep_time = flight_details[0].get('departure_time', '') if flight_details else ''
            arr_time = flight_details[-1].get('arrival_time', '') if flight_details else ''
            
            num_stops = len(flight_details) - 1 if flight_details else 0
            stops_airports = [f.get('departure_airport', {}).get('id', '') for f in flight_details[1:]] if len(flight_details) > 1 else []
            
            flights.append({
                'id': i,
                'flight_number': airline_info.get('flight_number', 'N/A'),
                'airline': airline_name,
                'airline_zh': airline_name,
                'origin': origin,
                'destination': destination,
                'departure_time': dep_time,
                'arrival_time': arr_time,
                'duration': total_duration // 60 if total_duration else 0,
                'stops': num_stops,
                'stops_airports': stops_airports,
                'price': price,
                'cabin_class': cabin_class,
                'aircraft': 'N/A',
                'seats_available': random.randint(1, 20),
            })
        
        flights.sort(key=lambda x: x['price'])
        return flights
        
    except Exception as e:
        print(f"SerpAPI error: {e}")
        return search_flights_mock(origin, destination, datetime.strptime(outbound_date, '%Y-%m-%d').date(), cabin_class)

def search_flights_mock(origin, destination, departure_date, cabin_class):
    flights = []
    base_prices = {
        'economy': {'direct': (400, 800), 'one_stop': (300, 600), 'two_stop': (250, 450)},
        'business': {'direct': (1500, 2500), 'one_stop': (1200, 2000), 'two_stop': (900, 1500)},
        'first': {'direct': (3000, 5000), 'one_stop': (2500, 4000), 'two_stop': (2000, 3500)},
    }
    
    flight_types = [
        {'type': 'direct', 'stops': 0},
        {'type': 'one_stop', 'stops': 1},
        {'type': 'two_stop', 'stops': 2},
    ]
    
    for i in range(15):
        for ft in flight_types:
            if random.random() > 0.6:
                continue
                
            dep_hour = random.randint(6, 22)
            dep_min = random.choice([0, 15, 30, 45])
            duration = random.randint(8, 18) + (ft['stops'] * 3)
            
            arr_hour = (dep_hour + duration) % 24
            dep_time = f"{dep_hour:02d}:{dep_min:02d}"
            arr_time = f"{arr_hour:02d}:{(dep_min + random.randint(0, 59)) % 60:02d}"
            
            price_range = base_prices[cabin_class][ft['type']]
            price = random.randint(int(price_range[0]), int(price_range[1]))
            
            airports = ['PVG', 'CDG', 'FRA', 'LHR', 'AMS', 'DXB']
            stops_airports = random.sample(airports, ft['stops']) if ft['stops'] > 0 else []
            
            flights.append({
                'id': i * 10 + ft['stops'],
                'flight_number': f"FL{random.randint(100, 999)}",
                'airline': 'Various Airlines',
                'airline_zh': '多家航空公司',
                'origin': origin,
                'destination': destination,
                'departure_time': dep_time,
                'arrival_time': arr_time,
                'duration': duration,
                'stops': ft['stops'],
                'stops_airports': stops_airports,
                'price': price,
                'cabin_class': cabin_class,
                'aircraft': random.choice(['Boeing 777', 'Airbus A350', 'Boeing 787', 'Airbus A380']),
                'seats_available': random.randint(1, 50),
            })
    
    flights.sort(key=lambda x: x['price'])
    return flights

def generate_price_history(origin, destination, target_date):
    history = []
    base_price = 500
    
    for i in range(60):
        day = target_date - timedelta(days=30 - i)
        fluctuation = random.uniform(0.85, 1.25)
        price = int(base_price * fluctuation)
        
        history.append({
            'date': day.isoformat(),
            'price': price,
            'day_of_week': day.strftime('%A'),
        })
    
    return history

def init_db():
    from flask import current_app
    from app.models.models import db
    with current_app.app_context():
        db.create_all()
        db.session.commit()
