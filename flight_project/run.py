# -*- coding: utf-8 -*-
import os
from flask import Flask
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
    from flask import jsonify
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Flight Search API",
            "version": "1.0",
            "description": "API for searching flights using SerpAPI"
        },
        "paths": {}
    }
    return jsonify(spec)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
