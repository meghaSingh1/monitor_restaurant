from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///restaurant_data.db'  # SQLite database for storing data
db = SQLAlchemy(app)

class StoreStatus(db.Model):
    store_id = db.Column(db.String, primary_key=True)
    timestamp_utc = db.Column(db.DateTime, primary_key=True)
    status = db.Column(db.String)

class StoreHours(db.Model):
    store_id = db.Column(db.String, primary_key=True)
    day_of_week = db.Column(db.Integer, primary_key=True)
    start_time_local = db.Column(db.Time)
    end_time_local = db.Column(db.Time)

class StoreTimezone(db.Model):
    store_id = db.Column(db.String, primary_key=True)
    timezone_str = db.Column(db.String)