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
    
    origin = data.get('origin', 'CDG')
    destination = data.get('destination', 'PEK')
    departure_date = data.get('departure_date')
    return_date = data.get('return_date')
    passengers = int(data.get('passengers', 1))
    cabin_class = data.get('cabin_class', 'economy')
    
    trip_type = int(data.get('type', 1))
    travel_class = int(data.get('travel_class', 1))
    adults = int(data.get('adults', 1))
    sort_by = int(data.get('sort_by', 1))
    stops = int(data.get('stops', 0))
    max_duration = int(data.get('max_duration', 1500))
    
    travel_class_to_cabin = {
        1: 'economy',
        2: 'premium_economy',
        3: 'business',
        4: 'first'
    }
    cabin_class = travel_class_to_cabin.get(travel_class, 'economy')
    
    if departure_date:
        departure_date_obj = datetime.strptime(departure_date, '%Y-%m-%d').date()
    else:
        return jsonify({'error': 'Missing departure_date'}), 400
    
    if trip_type == 1 and not return_date:
        return jsonify({'error': 'return_date is required for round trip'}), 400
    
    if trip_type == 1 and return_date:
        return_date_obj = datetime.strptime(return_date, '%Y-%m-%d').date()
    elif trip_type == 1:
        return_date_obj = (departure_date_obj + timedelta(days=14))
        return_date = return_date_obj.isoformat()
    else:
        return_date_obj = None
    
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
    
    if not USE_SERPAPI or not SERPAPI_API_KEY:
        return jsonify({'error': 'SerpAPI is not configured. Please set USE_SERPAPI=true and SERPAPI_API_KEY environment variables.'}), 500
    
    flights = search_flights_serpapi(
        origin, destination, departure_date, return_date, 
        cabin_class, passengers, trip_type, travel_class, 
        adults, sort_by, stops, max_duration
    )
    
    if flights is None:
        return jsonify({'error': 'SerpAPI request failed. Please check your API key and try again.'}), 500
    
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
            'cabin_class': cabin_class,
            'type': trip_type,
            'travel_class': travel_class,
            'adults': adults,
            'sort_by': sort_by,
            'stops': stops,
            'max_duration': max_duration
        },
        'data_source': 'serpapi'
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

def search_flights_serpapi(origin, destination, outbound_date, return_date, cabin_class, passengers=1, trip_type=1, travel_class=1, adults=1, sort_by=1, stops=0, max_duration=1500):
    from serpapi import Client
    
    if not SERPAPI_API_KEY:
        return None
    
    try:
        travel_class_map = {
            "economy": "1",
            "premium_economy": "2",
            "business": "3",
            "first": "4"
        }
        
        trip_type_map = {
            "round_trip": 1,
            "one_way": 2,
            "multi_city": 3
        }
        
        sort_by_map = {
            "best": "1",
            "price": "2",
            "duration": "3"
        }
        
        stops_map = {
            "any": None,
            "direct": 1,
            "1_stop": 2,
            "2_stops": 3
        }
        
        params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "currency": "EUR",
            "type": trip_type_map.get(trip_type, 1),
            "outbound_date": outbound_date,
            "travel_class": travel_class_map.get(travel_class, "1"),
            "adults": str(adults),
            "sort_by": sort_by_map.get(sort_by, "1"),
            "duration": "1500"
        }
        
        if trip_type == "round_trip" and return_date:
            params["return_date"] = return_date
        
        if stops != "any":
            params["max_stops"] = str(stops_map.get(stops, 1))
        
        client = Client(api_key=SERPAPI_API_KEY)
        results = client.search(params)
        
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
            
            first_segment = flight_details[0] if flight_details else {}
            last_segment = flight_details[-1] if flight_details else {}
            
            dep_airport = first_segment.get('departure_airport', {})
            arr_airport = last_segment.get('arrival_airport', {})
            
            dep_time = dep_airport.get('time', '') if dep_airport else ''
            arr_time = arr_airport.get('time', '') if arr_airport else ''
            
            num_stops = len(flight_details) - 1 if flight_details else 0
            
            layovers = flight.get('layovers', [])
            stops_airports = [layover.get('id', '') for layover in layovers]
            
            flight_number = first_segment.get('flight_number', 'N/A')
            airline = first_segment.get('airline', 'Unknown')
            airplane = first_segment.get('airplane', 'N/A')
            
            flights.append({
                'id': i,
                'flight_number': flight_number,
                'airline': airline,
                'airline_zh': airline,
                'origin': dep_airport.get('id', origin),
                'destination': arr_airport.get('id', destination),
                'departure_time': dep_time,
                'arrival_time': arr_time,
                'duration': total_duration // 60 if total_duration else 0,
                'stops': num_stops,
                'stops_airports': stops_airports,
                'price': price,
                'cabin_class': cabin_class,
                'aircraft': airplane,
                'seats_available': random.randint(1, 20),
                'type': flight.get('type', ''),
                'carbon_emissions': flight.get('carbon_emissions', {}),
            })
        
        sort_options = {
            1: lambda x: x['price'],
            2: lambda x: x['price'],
            3: lambda x: x['duration']
        }
        flights.sort(key=sort_options.get(sort_by, lambda x: x['price']))
        
        return flights
        
    except Exception as e:
        print(f"SerpAPI error: {e}")
        return None

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
