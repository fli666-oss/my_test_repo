# -*- coding: utf-8 -*-
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'dev-key-change-in-production'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flights.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    from app.models import models
    db = models.init_db(app)
    
    with app.app_context():
        from app.routes.main import main_bp, init_db
        app.register_blueprint(main_bp)
        init_db()
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
