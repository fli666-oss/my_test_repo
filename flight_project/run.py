# -*- coding: utf-8 -*-
import os
from flask import Flask
from flasgger import Swagger

def create_app():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    app = Flask(__name__,
                template_folder=os.path.join(base_dir, 'app', 'templates'),
                static_folder=os.path.join(base_dir, 'app', 'static'))
    app.config['SECRET_KEY'] = 'dev-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flights.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "static_folder": "static",
        "title": "Flight Search API",
        "version": "1.0",
        "description": "API for searching flights using SerpAPI",
    }
    
    swagger = Swagger(app, config=swagger_config)
    
    from app.models.models import db, init_db
    init_db(app)
    
    with app.app_context():
        from app.routes.main import main_bp, init_db as setup_db
        app.register_blueprint(main_bp)
        setup_db()
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
