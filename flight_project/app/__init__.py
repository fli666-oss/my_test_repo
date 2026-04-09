# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    from run import app
    db.init_app(app)
    with app.app_context():
        db.create_all()
    return app
