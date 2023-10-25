import os
import csv
import random
import secrets
import string
import pytz
from random import randint, choice
from datetime import datetime, timedelta, time
from flask import Flask, request, jsonify, send_file
from models import db, app, StoreStatus, StoreHours, StoreTimezone

with app.app_context():
    db.create_all()

# Define API endpoints
@app.route('/trigger_report', methods=['POST'])
def trigger_report():
    report_id = generate_report()
    return jsonify({"report_id": report_id})

@app.route('/get_report', methods=['GET'])
def get_report():
    report_id = request.args.get('report_id')
    if is_report_complete(report_id):
        report_data = generate_report_data(report_id)
        if report_data:
            return send_file(report_data, as_attachment=True, download_name='restaurant_report.csv')
    else:
        return "Running"

def generate_report():
    characters = string.ascii_letters + string.digits
    length = 5
    report_id = ''.join(secrets.choice(characters) for _ in range(length))
    sample_data()
    return report_id

def is_report_complete(report_id):
    return True

def generate_report_data(report_id):
    report_data = calculate_report_data()
    file_path = "restaurant_report.csv"
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(report_data)
    return file_path

def sample_data():
    stores = ["Store1", "Store2", "Store3", "Store4"]
    statuses = ["active", "inactive"]
    timezones = ["Asia/Kolkata", "America/New_York", "America/Los_Angeles", "America/Chicago", "America/Denver"]
    timezone_flag = 0
    for store in stores:
        for i in range(1, 8):  # For 7 days of the week
            for hour in range(0, 24):
                timestamp_utc = datetime(2023, 10, i, hour, 0)
                status = random.choice(statuses)
                store_data = StoreStatus(store_id=store, timestamp_utc=timestamp_utc, status=status)
                db.session.add(store_data)
            start_time_local = time(9, 0)
            end_time_local = time(i + 14, 0)
            store_hours = StoreHours(store_id=store, start_time_local=start_time_local, end_time_local=end_time_local, day_of_week=i)
            db.session.add(store_hours)
        store_timezone = StoreTimezone(store_id=store, timezone_str=timezones[timezone_flag])  # Use the correct attribute
        timezone_flag += 1
        db.session.add(store_timezone)

    db.session.commit()

def calculate_report_data():
    report_data = [
        ["store_id", "uptime_last_hour", "uptime_last_day", "update_last_week", "downtime_last_hour", "downtime_last_day", "downtime_last_week"]
    ]
    stores = ["Store1", "Store2", "Store3", "Store4"]

    for store in stores:
        uptime_last_hour = 0
        uptime_last_day = 0
        uptime_last_week = 0
        downtime_last_hour = 0
        downtime_last_day = 0
        downtime_last_week = 0
        data = StoreStatus.query.filter_by(store_id=store).order_by(StoreStatus.timestamp_utc).all()
        store_timezone = StoreTimezone.query.filter_by(store_id=store).first()
        if not store_timezone:
            store_timezone = "Asia/Kolkata" 

        hours = StoreHours.query.filter_by(store_id=store).all()

        for i in range(len(data) - 1):
            entry1 = data[i]
            entry2 = data[i + 1]
            time_difference = (entry2.timestamp_utc - entry1.timestamp_utc).total_seconds() / 60  # minutes

            # Convert timestamps to the store's local time based on the timezone
            entry1_local_time = entry1.timestamp_utc.astimezone(pytz.timezone(store_timezone.timezone_str))
            entry2_local_time = entry2.timestamp_utc.astimezone(pytz.timezone(store_timezone.timezone_str))

            # Get the store hours for the day of entry1_local_time
            store_hours_for_day = [hour_entry for hour_entry in hours if hour_entry.day_of_week == entry1_local_time.weekday()]

            if store_hours_for_day:
                # Only perform calculations if there are store hours for the day
                day_start_time = store_hours_for_day[0].start_time_local
                day_end_time = store_hours_for_day[0].end_time_local

                # Check if entry1 and entry2 fall within the business hours for this day
                if day_start_time <= entry1_local_time.time() < day_end_time and day_start_time <= entry2_local_time.time() < day_end_time:
                    # The entries fall within business hours
                    if entry1.status == "inactive" and entry2.status == "active":
                        if uptime_last_week + time_difference <= 10080:
                            uptime_last_week += time_difference
                        if time_difference <= 60 and (uptime_last_day + time_difference) < 60:
                            uptime_last_hour += time_difference
                        else:
                            uptime_last_hour = 60
                        if (uptime_last_day + time_difference <= 1440):
                            uptime_last_day += time_difference
                        else:
                            uptime_last_day = 1440
                    else:
                        if downtime_last_week + time_difference <= 10080:
                            downtime_last_week += time_difference
                        if time_difference <= 60 and (downtime_last_day + time_difference) < 60:
                            downtime_last_hour += time_difference
                        else:
                            downtime_last_hour = 60
                        if (downtime_last_day + time_difference <= 1440):
                            downtime_last_day += time_difference
                        else:
                            downtime_last_day = 1440
        report_data.append([store, uptime_last_hour, uptime_last_day, uptime_last_week, downtime_last_hour, downtime_last_day, downtime_last_week])
        # returned time is in minutes
    return report_data


if __name__ == '__main__':
    app.run(debug=True)
