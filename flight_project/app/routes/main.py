# -*- coding: utf-8 -*-
from flask import Blueprint, render_template, request, jsonify
from datetime import datetime, date, timedelta
import os
import random
import logging
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flight_search.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

main_bp = Blueprint('main', __name__)

USE_SERPAPI = os.environ.get('USE_SERPAPI', 'false').lower() == 'true'
SERPAPI_API_KEY = os.environ.get('SERPAPI_API_KEY', '')

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/search', methods=['POST'])
def search_flights():
    """
    Search for flights using SerpAPI
    ---
    tags:
      - Flights
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - departure_id
            - arrival_id
            - outbound_date
          properties:
            departure_id:
              type: string
              example: "CDG"
              description: "Departure airport code (e.g., CDG, PEK, LHR)"
            arrival_id:
              type: string
              example: "PEK"
              description: "Arrival airport code (e.g., PEK, CDG, LHR)"
            outbound_date:
              type: string
              example: "2026-05-01"
              description: "Departure date (YYYY-MM-DD)"
            return_date:
              type: string
              example: "2026-05-15"
              description: "Return date for round trip (YYYY-MM-DD)"
            type:
              type: string
              example: "1"
              description: "Trip type: 	1 - Round trip (default), 2 - One way, 3 - Multi-city"
            travel_class:
              type: string
              example: "1"
              description: "Cabin class: 1 - Economy (default),	2 - Premium Economy, 3 - Business, 4 - Firs"
            adults:
              type: integer
              example: 1
              description: "Number of adult passengers"
            sort_by:
              type: string
              example: "5"
              description: "Sort by: 1 - Top flights (default), 2 - Price,	5 - Duration"
            stops:
              type: string
              example: "1"
              description: "Stops: , 0-Any, 1-direct, 2-1_stop, 3-2_stops"
    responses:
      200:
        description: Flight search results
        schema:
          type: object
          properties:
            flights:
              type: array
            search_info:
              type: object
            data_source:
              type: string
      400:
        description: Missing required parameters
      500:
        description: SerpAPI error or not configured
    """
    from app.models.models import db, SearchHistory, FlightPrice
    data = request.get_json()
    
    logger.info(f"Received search request: {json.dumps(data, ensure_ascii=False)}")
    
    origin = data.get('origin', 'CDG')
    destination = data.get('destination', 'PEK')
    departure_date = data.get('departure_date')
    return_date = data.get('return_date')
    passengers = int(data.get('passengers', 1))
    
    trip_type = data.get('type', 'round_trip')
    travel_class = data.get('travel_class', 'economy')
    adults = int(data.get('passengers', 1))
    sort_by = data.get('sort_by', 'best')
    stops = data.get('stops', 'any')
    
    travel_class_to_cabin = {
        'economy': 'economy',
        'premium_economy': 'premium_economy',
        'business': 'business',
        'first': 'first'
    }
    cabin_class = travel_class_to_cabin.get(travel_class, 'economy')
    
    travel_class_to_num = {
        'economy': 1,
        'premium_economy': 2,
        'business': 3,
        'first': 4
    }
    trip_type_to_num = {
        'round_trip': 1,
        'one_way': 2,
        'multi_city': 3
    }
    sort_by_to_num = {
        'best': 1,
        'price': 2,
        'duration': 3
    }
    stops_to_num = {
        'any': 0,
        'direct': 1,
        '1_stop': 2,
        '2_stops': 3
    }
    
    trip_type_num = trip_type_to_num.get(trip_type, 1)
    
    if departure_date:
        departure_date_obj = datetime.strptime(departure_date, '%Y-%m-%d').date()
    else:
        return jsonify({'error': 'Missing departure_date'}), 400
    
    if trip_type_num == 1 and not return_date:
        return jsonify({'error': 'return_date is required for round trip'}), 400
    
    if trip_type_num == 1 and return_date:
        return_date_obj = datetime.strptime(return_date, '%Y-%m-%d').date()
    elif trip_type_num == 1:
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
        adults, sort_by, stops
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
            'stops': stops
        },
        'data_source': 'serpapi'
    })

@main_bp.route('/search-serpapi', methods=['POST'])
def search_serpapi_direct():
    """
    Search flights using SerpAPI with direct parameters
    ---
    tags:
      - Flights
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - api_key
            - departure_id
            - arrival_id
            - outbound_date
          properties:
            api_key:
              type: string
              example: "your_api_key"
            engine:
              type: string
              default: "google_flights"
            departure_id:
              type: string
              example: "PEK"
            arrival_id:
              type: string
              example: "CDG"
            outbound_date:
              type: string
              example: "2026-04-24"
            return_date:
              type: string
              example: "2026-04-30"
            travel_class:
              type: string
              default: "1"
            type:
              type: string
              default: "1"
            adults:
              type: string
              default: "1"
            sort_by:
              type: string
              default: "1"
            departure_token:
              type: string
            output:
              type: string
              description: "Output file path (optional)"
    responses:
      200:
        description: Raw SerpAPI response
      400:
        description: Missing required parameters
      500:
        description: API error
    """
    from serpapi import Client
    
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No JSON data provided'}), 400
    
    api_key = data.get('api_key')
    if not api_key:
        return jsonify({'error': 'api_key is required'}), 400
    
    departure_id = data.get('departure_id')
    arrival_id = data.get('arrival_id')
    outbound_date = data.get('outbound_date')
    
    if not departure_id or not arrival_id or not outbound_date:
        return jsonify({'error': 'departure_id, arrival_id, and outbound_date are required'}), 400
    
    params = {
        "engine": data.get('engine', 'google_flights'),
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "outbound_date": outbound_date,
    }
    
    optional_fields = ['return_date', 'travel_class', 'type', 'adults', 'sort_by', 'departure_token', 'currency', 'duration']
    for field in optional_fields:
        if data.get(field):
            params[field] = data[field]
    
    logger.info(f"Direct SerpAPI request: {json.dumps(params, ensure_ascii=False)}")
    
    try:
        client = Client(api_key=api_key)
        results = client.search(params)
        results_dict = dict(results)
        
        logger.info(f"Response keys: {list(results_dict.keys())}")
        
        output_file = data.get('output')
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results_dict, f, ensure_ascii=False, indent=2)
            logger.info(f"Results saved to: {output_file}")
        
        return jsonify(results_dict)
    
    except Exception as e:
        logger.error(f"SerpAPI error: {e}")
        return jsonify({'error': str(e)}), 500

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

def search_flights_serpapi(origin, destination, outbound_date, return_date, cabin_class, passengers=1, trip_type='round_trip', travel_class='economy', adults=1, sort_by='best', stops='any'):
    from serpapi import Client
    
    if not SERPAPI_API_KEY:
        return None
    
    try:
        travel_class_map = {
            'economy': "1",
            'premium_economy': "2",
            'business': "3",
            'first': "4"
        }
        
        trip_type_map = {
            'round_trip': "1",
            'one_way': "2",
            'multi_city': "3"
        }
        
        sort_by_map = {
            'best': "1",
            'price': "2",
            'duration': "5"
        }
        
        stops_map = {
            'any': "0",
            'direct': "1",
            '1_stop': "2",
            '2_stops': "3"
        }
        
        params = {
            "engine": "google_flights",
            "departure_id": origin,
            "arrival_id": destination,
            "currency": "EUR",
            "type": trip_type_map.get(trip_type, "1"),
            "outbound_date": outbound_date,
            "travel_class": travel_class_map.get(travel_class, "1"),
            "adults": str(adults),
            "sort_by": sort_by_map.get(sort_by, "1"),
            "duration": "1500"
        }
        
        if trip_type == 'round_trip' and return_date:
            params["return_date"] = return_date
        
        if stops != 'any':
            params["max_stops"] = stops_map.get(stops, "1")
        
        logger.info(f"SerpAPI request params: {json.dumps(params, ensure_ascii=False)}")
        
        client = Client(api_key=SERPAPI_API_KEY)
        outbound_results = client.search(params)
        
        logger.info(f"Outbound response keys: {list(outbound_results.keys())}")
        
        outbound_flights = []
        return_flights = outbound_results.get('best_flights', []) + outbound_results.get('other_flights', [])
        
        for i, flight in enumerate(return_flights):
            flight_details = flight.get('flights', [])
            total_duration = flight.get('total_duration', 0)
            price = flight.get('price', 0)
            departure_token = flight.get('departure_token', '')
            
            if not price:
                continue
            
            first_segment = flight_details[0] if flight_details else {}
            last_segment = flight_details[-1] if flight_details else {}
            
            dep_airport = first_segment.get('departure_airport', {})
            arr_airport = last_segment.get('arrival_airport', {})
            
            outbound_segments = []
            for seg in flight_details:
                seg_dep = seg.get('departure_airport', {})
                seg_arr = seg.get('arrival_airport', {})
                outbound_segments.append({
                    'flight_number': seg.get('flight_number', 'N/A'),
                    'airline': seg.get('airline', 'Unknown'),
                    'airline_logo': seg.get('airline_logo', ''),
                    'aircraft': seg.get('airplane', 'N/A'),
                    'departure_airport': seg_dep.get('id', ''),
                    'departure_time': seg_dep.get('time', ''),
                    'arrival_airport': seg_arr.get('id', ''),
                    'arrival_time': seg_arr.get('time', ''),
                    'duration': seg.get('duration', 0),
                })
            
            layovers = flight.get('layovers', [])
            
            flight_data = {
                'id': i,
                'price': price,
                'cabin_class': cabin_class,
                'type': flight.get('type', ''),
                'carbon_emissions': flight.get('carbon_emissions', {}),
                'total_duration': total_duration,
                'extensions': flight.get('extensions', []),
                'outbound_flights': outbound_segments,
                'outbound_stops': len(flight_details) - 1 if flight_details else 0,
                'outbound_layovers': layovers,
                'departure_token': departure_token,
            }
            
            if trip_type == 'round_trip' and return_date and departure_token:
                return_params = {
                    "engine": "google_flights",
                    "departure_id": origin,
                    "arrival_id": destination,
                    "currency": "EUR",
                    "type": trip_type_map.get(trip_type, "1"),
                    "outbound_date": outbound_date,
                    "return_date": return_date,
                    "travel_class": travel_class_map.get(travel_class, "1"),
                    "adults": adults,
                    "departure_token": departure_token,
                }
                client = Client(api_key=SERPAPI_API_KEY)
                logger.info(f"Fetching return flights with token...")
                logger.info(f"2nd search params : {return_params}")
                try:
                    return_results = client.search(return_params)
                    results_dict = dict(return_results)
                    logger.info(f"Response keys: {list(results_dict.keys())}")
                    logger.info(f"return_results : {results_dict}")
                    return_flights = results_dict.get('best_flights', []) + results_dict.get('other_flights', [])
                    
                    if return_flights and len(return_flights) > 0:
                        ret_flight = return_flights[0]
                        ret_details = ret_flight.get('flights', [])
                        
                        return_segments = []
                        for seg in ret_details:
                            seg_dep = seg.get('departure_airport', {})
                            seg_arr = seg.get('arrival_airport', {})
                            return_segments.append({
                                'flight_number': seg.get('flight_number', 'N/A'),
                                'airline': seg.get('airline', 'Unknown'),
                                'airline_logo': seg.get('airline_logo', ''),
                                'aircraft': seg.get('airplane', 'N/A'),
                                'departure_airport': seg_dep.get('id', ''),
                                'departure_time': seg_dep.get('time', ''),
                                'arrival_airport': seg_arr.get('id', ''),
                                'arrival_time': seg_arr.get('time', ''),
                                'duration': seg.get('duration', 0),
                            })
                        
                        flight_data['return_flights'] = return_segments
                        flight_data['return_stops'] = len(ret_details) - 1 if ret_details else 0
                        flight_data['return_layovers'] = ret_flight.get('layovers', [])
                        flight_data['return_duration'] = ret_flight.get('total_duration', 0)
                        flight_data['return_carbon_emissions'] = ret_flight.get('carbon_emissions', {})
                        
                except Exception as e:
                    logger.error(f"Error fetching return flights: {e}")
            
            outbound_flights.append(flight_data)
        
        sort_options = {
            'best': lambda x: x['price'],
            'price': lambda x: x['price'],
            'duration': lambda x: x.get('total_duration', 0)
        }
        outbound_flights.sort(key=sort_options.get(sort_by, lambda x: x['price']))
        
        return outbound_flights
        
    except Exception as e:
        logger.error(f"SerpAPI error: {e}")
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
