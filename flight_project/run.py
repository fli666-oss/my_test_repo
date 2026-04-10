# -*- coding: utf-8 -*-
import os
from flask import Flask, jsonify
from flask_swagger_ui import get_swaggerui_blueprint

def create_app():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app = Flask(__name__,
                template_folder=os.path.join(base_dir, 'app', 'templates'),
                static_folder=os.path.join(base_dir, 'app', 'static'))
    app.config['SECRET_KEY'] = 'dev-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flights.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
        "/apidocs",
        "/apispec.json",
        config={
            "app_name": "Flight Search API"
        }
    )
    app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix="/apidocs")
    
    from app.models.models import db, init_db
    init_db(app)
    
    with app.app_context():
        from app.routes.main import main_bp, init_db as setup_db
        app.register_blueprint(main_bp)
        setup_db()
    
    return app

app = create_app()

@app.route("/apispec.json")
def create_api_spec():
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Flight Search API",
            "version": "1.0",
            "description": "API for searching flights using SerpAPI"
        },
        "servers": [
            {"url": "http://localhost:5000", "description": "Local server"}
        ],
        "paths": {
            "/search": {
                "post": {
                    "tags": ["Flights"],
                    "summary": "Search for flights using SerpAPI",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["origin", "destination", "departure_date"],
                                    "properties": {
                                        "origin": {"type": "string", "example": "CDG"},
                                        "destination": {"type": "string", "example": "PEK"},
                                        "departure_date": {"type": "string", "example": "2026-05-01"},
                                        "return_date": {"type": "string", "example": "2026-05-15"},
                                        "type": {"type": "string", "example": "1", "description": "1-Round trip, 2-One way, 3-Multi-city"},
                                        "travel_class": {"type": "string", "example": "1", "description": "1-Economy, 2-Premium Economy, 3-Business, 4-First"},
                                        "adults": {"type": "integer", "example": 1},
                                        "sort_by": {"type": "string", "example": "1", "description": "1-Top flights, 2-Price, 5-Duration"},
                                        "stops": {"type": "string", "example": "0", "description": "0-Any, 1-Direct, 2-1 stop, 3-2 stops"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Flight search results"},
                        "400": {"description": "Missing required parameters"},
                        "500": {"description": "SerpAPI error or not configured"}
                    }
                }
            },
            "/search-serpapi": {
                "post": {
                    "tags": ["Flights"],
                    "summary": "Search flights using SerpAPI with direct parameters",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["api_key", "departure_id", "arrival_id", "outbound_date"],
                                    "properties": {
                                        "api_key": {"type": "string", "example": "your_api_key"},
                                        "engine": {"type": "string", "default": "google_flights"},
                                        "departure_id": {"type": "string", "example": "PEK"},
                                        "arrival_id": {"type": "string", "example": "CDG"},
                                        "outbound_date": {"type": "string", "example": "2026-04-24"},
                                        "return_date": {"type": "string", "example": "2026-04-30"},
                                        "travel_class": {"type": "string", "default": "1"},
                                        "type": {"type": "string", "default": "1"},
                                        "adults": {"type": "string", "default": "1"},
                                        "sort_by": {"type": "string", "default": "1"},
                                        "departure_token": {"type": "string"},
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Raw SerpAPI response"},
                        "400": {"description": "Missing required parameters"},
                        "500": {"description": "API error"}
                    }
                }
            },
            "/price-history": {
                "get": {
                    "tags": ["Flights"],
                    "summary": "Get price history for a route",
                    "parameters": [
                        {"name": "origin", "in": "query", "schema": {"type": "string", "default": "PEK"}},
                        {"name": "destination", "in": "query", "schema": {"type": "string", "default": "CDG"}},
                        {"name": "departure_date", "in": "query", "schema": {"type": "string"}},
                        {"name": "cabin_class", "in": "query", "schema": {"type": "string", "default": "economy"}}
                    ],
                    "responses": {
                        "200": {"description": "Price history data"}
                    }
                }
            },
            "/airlines": {
                "get": {
                    "tags": ["Flights"],
                    "summary": "Get list of airlines",
                    "responses": {
                        "200": {"description": "List of airlines"}
                    }
                }
            }
        }
    }
    return jsonify(spec)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
