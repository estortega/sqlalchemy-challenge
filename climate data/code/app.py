# Import the dependencies.
import numpy as np
import pandas as pd
import datetime as dt
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.automap import automap_base


#################################################
# Database Setup
#################################################

# Create engine using the `hawaii.sqlite` database file
engine = create_engine("sqlite:///hawaii.sqlite")
# Declare a Base using `automap_base()`
base = automap_base()
# Use the Base class to reflect the database tables
base.prepare(autoload_with = engine)

# Assign the measurement class to a variable called `Measurement` and
# the station class to a variable called `Station`
measurement = base.classes.measurement
station = base.classes.station

# Create a session
session = Session(engine)

#################################################
# Flask Setup
#################################################

app = Flask(__name__)

#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"Welcome to the Climate API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation - Last 12 months of precipitation data<br/>"
        f"/api/v1.0/stations - List of weather stations<br/>"
        f"/api/v1.0/tobs - Temperature observations for the most active station<br/>"
        f"/api/v1.0/&lt;start&gt; - Min, Avg, Max temperature from a start date<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt; - Min, Avg, Max temperature between start and end dates<br/>"
    )

# Precipitation Route
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the last 12 months of precipitation data as JSON."""
    session = Session(engine)
    
    # Get the most recent date in the dataset
    latest_date = session.query(func.max(measurement.date)).scalar()
    latest_date = dt.datetime.strptime(latest_date, "%Y-%m-%d")
    one_year_ago = latest_date - dt.timedelta(days=365)

    # Query last 12 months of precipitation data
    results = session.query(measurement.date, measurement.prcp).\
        filter(measurement.date >= one_year_ago).all()
    
    session.close()

    # Convert to dictionary format
    precipitation_data = {date: prcp for date, prcp in results}
    return jsonify(precipitation_data)

# Stations Route
@app.route("/api/v1.0/stations")
def stations():
    """Return a list of stations as JSON."""
    session = Session(engine)
    results = session.query(station.station).all()
    session.close()

    # Convert to a list
    stations_list = [station[0] for station in results]
    return jsonify(stations_list)

# Temperature Observations Route
@app.route("/api/v1.0/tobs")
def tobs():
    """Return temperature observations for the most active station in the last year."""
    session = Session(engine)

    # Find the most active station
    most_active_station = session.query(
        measurement.station, func.count(measurement.station)
    ).group_by(measurement.station).order_by(func.count(measurement.station).desc()).first()[0]

    # Get latest date and compute 1 year back
    latest_date = session.query(func.max(measurement.date)).scalar()
    latest_date = dt.datetime.strptime(latest_date, "%Y-%m-%d")
    one_year_ago = latest_date - dt.timedelta(days=365)

    # Query temperature data for the most active station
    results = session.query(measurement.date, measurement.tobs).\
        filter(measurement.station == most_active_station).\
        filter(measurement.date >= one_year_ago).all()

    session.close()

    # Convert to list of dictionaries
    tobs_data = [{"date": date, "temperature": tobs} for date, tobs in results]
    return jsonify(tobs_data)

# Temperature Stats Route (Start Date Only)
@app.route("/api/v1.0/<start>")
def temp_stats_start(start):
    """Return min, avg, and max temperatures for dates greater than or equal to start."""
    session = Session(engine)

    results = session.query(
        func.min(measurement.tobs),
        func.avg(measurement.tobs),
        func.max(measurement.tobs)
    ).filter(measurement.date >= start).all()

    session.close()

    # Extract results
    temp_data = {
        "start_date": start,
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }

    return jsonify(temp_data)

# Temperature Stats Route (Start & End Date)
@app.route("/api/v1.0/<start>/<end>")
def temp_stats_range(start, end):
    """Return min, avg, and max temperatures for a date range."""
    session = Session(engine)

    results = session.query(
        func.min(measurement.tobs),
        func.avg(measurement.tobs),
        func.max(measurement.tobs)
    ).filter(measurement.date >= start).filter(measurement.date <= end).all()

    session.close()

    # Extract results
    temp_data = {
        "start_date": start,
        "end_date": end,
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2]
    }

    return jsonify(temp_data)

# Run the application
if __name__ == "__main__":
    app.run(debug=True)