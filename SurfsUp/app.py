# Import the dependencies
from flask import Flask, jsonify
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
import os
from datetime import datetime, timedelta




#################################################
# Database Setup
#################################################

# Get the directory of the Flask app file (SurfsUp folder)
app_path = os.path.dirname(os.path.abspath(__file__))

# Specify the name of your SQLite database file
database_filename = 'hawaii.sqlite'

# Specify the name of the folder containing the database file
database_folder = 'Resources'

# Construct the absolute path to the database file
database_path = os.path.abspath(os.path.join(app_path, '..', database_folder, database_filename))

# Create the SQLAlchemy engine with the absolute path
engine = create_engine('sqlite:///' + database_path)

# Check if the database file exists
if not os.path.isfile(database_path):
    print(f"Error: Database file not found at '{database_path}'.")
else:
    print(f"Database file found at '{database_path}'.")

# Reflect an existing database into a new model
Base = automap_base()

# Reflect the tables
Base.prepare(engine, reflect=True)


# Save references to each table
Station = Base.classes.station
Measurement = Base.classes.measurement

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



#################################################
# Flask Routes
#################################################
@app.route("/")
def home():
    """Homepage with a list of available routes."""
    return (
        f"Welcome to the Climate App!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Calculate the date one year ago from the most recent date in the dataset
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = datetime.strptime(most_recent_date, "%Y-%m-%d") - timedelta(days=365)
    
    # Query to retrieve the last 12 months of precipitation data
    results = session.query(Measurement.date, Measurement.prcp).\
        filter(Measurement.date >= one_year_ago).all()
    
    # Convert the query results to a dictionary
    precipitation_data = {date: prcp for date, prcp in results}

    return jsonify(precipitation_data)

@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""
    # Query to retrieve the list of stations
    results = session.query(Station.station).all()
    
    # Convert the query results to a list
    station_list = [station for (station,) in results]

    return jsonify(station_list)

@app.route("/api/v1.0/tobs")
def tobs():
    # Using the most active station ID from the previous query
    most_active_station_id = session.query(Measurement.station).\
        group_by(Measurement.station).\
        order_by(func.count(Measurement.station).desc()).first()[0]

    # Calculate the date one year ago from the most recent date in the dataset
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    one_year_ago = datetime.strptime(most_recent_date, "%Y-%m-%d") - timedelta(days=365)

    # Query to retrieve the last 12 months of temperature observation data for the most active station
    temperature_data = session.query(Measurement.date, Measurement.tobs).\
        filter(Measurement.station == most_active_station_id).\
        filter(Measurement.date >= one_year_ago).all()

    # Convert the query results to a list of dictionaries
    temperature_list = [{"date": date, "temperature": tobs} for date, tobs in temperature_data]

    return jsonify(temperature_list)

@app.route("/api/v1.0/<start>")
def temp_start(start):
    """Return a JSON list of temperature statistics for a specified start date."""
    # Query to calculate temperature statistics for the dates greater than or equal to the start date
    temperature_stats = session.query(func.min(Measurement.tobs).label('min_temp'),
                                      func.max(Measurement.tobs).label('max_temp'),
                                      func.avg(Measurement.tobs).label('avg_temp')).\
        filter(Measurement.date >= start).all()

    # Convert the query results to a dictionary
    temp_stats_dict = {
        "min_temperature": temperature_stats[0][0],
        "max_temperature": temperature_stats[0][1],
        "avg_temperature": temperature_stats[0][2]
    }

    return jsonify(temp_stats_dict)

@app.route("/api/v1.0/<start>/<end>")
def temp_start_end(start, end):
    """Return a JSON list of temperature statistics for a specified start and end date range."""
    # Query to calculate temperature statistics for the dates from the start date to the end date, inclusive
    temperature_stats = session.query(func.min(Measurement.tobs).label('min_temp'),
                                      func.max(Measurement.tobs).label('max_temp'),
                                      func.avg(Measurement.tobs).label('avg_temp')).\
        filter(Measurement.date >= start).\
        filter(Measurement.date <= end).all()

    # Convert the query results to a dictionary
    temp_stats_dict = {
        "min_temperature": temperature_stats[0][0],
        "max_temperature": temperature_stats[0][1],
        "avg_temperature": temperature_stats[0][2]
    }

    return jsonify(temp_stats_dict)

# Run the Flask app
app.run