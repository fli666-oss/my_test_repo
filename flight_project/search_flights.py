# -*- coding: utf-8 -*-
import json
import logging
import sys
from serpapi import Client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('flight_search.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_params_from_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def search_flights(api_key, origin, destination, departure_date, return_date=None, 
                   travel_class='1', trip_type='1', adults=1, 
                   sort_by='1', stops=None):
    
    if not api_key:
        logger.error("API key not provided")
        return None
    
    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "currency": "EUR",
        "type": trip_type,
        "outbound_date": departure_date,
        "travel_class": travel_class,
        "adults": str(adults),
        "sort_by": sort_by,
        "duration": "1500"
    }
    
    if return_date:
        params["return_date"] = return_date
    
    if stops:
        params["max_stops"] = stops
    
    logger.info(f"Searching flights: {origin} -> {destination}")
    logger.info(f"Request params: {json.dumps(params)}")
    
    try:
        client = Client(api_key=api_key)
        results = client.search(params)
        
        logger.info(f"Response keys: {list(results.keys())}")
        return results
        
    except Exception as e:
        logger.error(f"SerpAPI error: {e}")
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python search_flights.py <params.json>")
        sys.exit(1)
    
    params_file = sys.argv[1]
    
    logger.info(f"Loading parameters from: {params_file}")
    params = load_params_from_file(params_file)
    
    api_key = params.get('api_key')
    if not api_key:
        print("Error: api_key is required in params file")
        sys.exit(1)
    
    if not params.get('departure_date'):
        print("Error: departure_date is required")
        sys.exit(1)
    
    logger.info(f"Search parameters: {json.dumps(params, ensure_ascii=False)}")
    
    results = search_flights(
        api_key=api_key,
        origin=params.get('origin', 'PEK'),
        destination=params.get('destination', 'CDG'),
        departure_date=params['departure_date'],
        return_date=params.get('return_date'),
        travel_class=params.get('travel_class', '1'),
        trip_type=params.get('trip_type', '1'),
        adults=params.get('adults', 1),
        sort_by=params.get('sort_by', '1'),
        stops=params.get('stops')
    )
    
    output_file = params.get('output', 'flights_result.json')
    
    if results:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"Results saved to: {output_file}")
    else:
        print("No results")
        sys.exit(1)

if __name__ == '__main__':
    main()
