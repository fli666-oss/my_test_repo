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

def search_flights(api_key, departure_id, arrival_id, outbound_date, return_date=None, 
                   currency="EUR", type="1", adults="1", 
                   departure_token=None, travel_class="1", sort_by="1", duration="1500"):
    
    if not api_key:
        logger.error("API key not provided")
        return None
    
    params = {
        "engine": "google_flights",
        "departure_id": departure_id,
        "arrival_id": arrival_id,
        "currency": currency,
        "type": type,
        "outbound_date": outbound_date,          
        "adults": adults,
        "travel_class": travel_class,
        "sort_by": sort_by,
        "duration": duration


    }
    
    if return_date:
        params["return_date"] = return_date
    
    if departure_token:
        params["departure_token"] = departure_token
    
    logger.info(f"Searching flights: {departure_id} -> {arrival_id}")
    logger.info(f"Request params: {json.dumps(params)}")
    
    try:
        client = Client(api_key=api_key)
        results = client.search(params)
        
        results_dict = dict(results)
        
        logger.info(f"Response keys: {list(results_dict.keys())}")
        return results_dict
        
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
    
    if not params.get('outbound_date'):
        print("Error: outbound_date is required")
        sys.exit(1)
    
    logger.info(f"Search parameters: {json.dumps(params, ensure_ascii=False)}")
    
    results = search_flights(
        api_key=api_key,
        departure_id=params.get('departure_id', 'PEK'),
        arrival_id=params.get('arrival_id', 'CDG'),
        outbound_date=params['outbound_date'],
        return_date=params.get('return_date'),
        currency=params.get('currency', 'EUR'),
        type=params.get('type', '1'),
        adults=params.get('adults', '1'),
        departure_token=params.get('departure_token'),
        travel_class=params.get('travel_class', '1'),
        sort_by=params.get('sort_by', '1'),
        duration=params.get('duration', '1500')
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
