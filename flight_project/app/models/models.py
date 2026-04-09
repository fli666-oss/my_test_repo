# -*- coding: utf-8 -*-
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Airline(db.Model):
    __tablename__ = 'airlines'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    name_cn = db.Column(db.String(100))

class Flight(db.Model):
    __tablename__ = 'flights'
    id = db.Column(db.Integer, primary_key=True)
    flight_number = db.Column(db.String(20), nullable=False)
    airline_code = db.Column(db.String(10), db.ForeignKey('airlines.code'))
    origin = db.Column(db.String(10), nullable=False)
    destination = db.Column(db.String(10), nullable=False)
    departure_time = db.Column(db.String(10), nullable=False)
    arrival_time = db.Column(db.String(10), nullable=False)
    is_direct = db.Column(db.Boolean, default=True)
    stops = db.Column(db.Integer, default=0)
    aircraft_type = db.Column(db.String(50))

class FlightPrice(db.Model):
    __tablename__ = 'flight_prices'
    id = db.Column(db.Integer, primary_key=True)
    flight_id = db.Column(db.Integer, db.ForeignKey('flights.id'))
    departure_date = db.Column(db.Date, nullable=False)
    cabin_class = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='CNY')
    available_seats = db.Column(db.Integer)
    search_date = db.Column(db.DateTime, default=datetime.utcnow)

class SearchHistory(db.Model):
    __tablename__ = 'search_history'
    id = db.Column(db.Integer, primary_key=True)
    origin = db.Column(db.String(10), nullable=False)
    destination = db.Column(db.String(10), nullable=False)
    departure_date = db.Column(db.Date, nullable=False)
    return_date = db.Column(db.Date)
    passengers = db.Column(db.Integer, default=1)
    cabin_class = db.Column(db.String(20), default='economy')
    search_timestamp = db.Column(db.DateTime, default=datetime.utcnow)

def init_db(app):
    db.init_app(app)
    return db
