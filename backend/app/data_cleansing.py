import os
import logging
from pkgutil import get_data
from dotenv import load_dotenv
import pandas as pd
import pandas.io.sql as psql
from sqlalchemy import create_engine
from math import cos, asin, sqrt
import csv

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
HOST_DB = os.getenv('HOST_DB')
DB_NAME = os.getenv('DB_NAME')
ERROR_LOG_FILE_PATH = os.getenv('ERROR_LOG_FILE_PATH')
CSV_PATH = os.getenv('CSV_PATH')

MAX_SPEED_IN_HARBOR = 8
MAX_POINTS_IN_HARBOR = 20
MAX_DIST_IN_HARBOR = 1.08
MINIMUM_POINTS_IN_TRIP = 500
MAX_DIST = 2
MIN_TIME = 10

class Trip:
    def __init__(self, mmsi):
        self.mmsi = mmsi
        self.point_list = []
    
    def add_point_to_trip(self, point):
        self.point_list.append(point)
    
    def insert_point_list(self, point_list):
        self.point_list = point_list
    
    def get_points_in_trip(self):
        return self.point_list
    
    def remove_point_from_trip(self, point):
        self.point_list.remove(point)
    
    def remove_all_points_from_trip(self):
        self.point_list = []
    
    def get_mmsi(self):
        return self.mmsi
    
class Point:
    def __init__(self, longitude, latitude, sog, mmsi, timestamp):
        self.longitude = longitude
        self.latitude = latitude
        self.sog = sog
        self.mmsi = mmsi
        self.timestamp = timestamp
    
    def get_mmsi(self):
        return self.mmsi

    def get_timestamp(self):
        return self.timestamp
    
    def get_sog(self):
        return self.sog
    
# https://stackoverflow.com/questions/27928/calculate-distance-between-two-latitude-longitude-points-haversine-formula
# Returns the distance in nautical miles (NM)
def lat_long_distance(p1, p2):
    km_to_nm = 0.53
    p_rad = 0.017        # pi / 180
    a = 0.5 - cos((p2.latitude - p1.latitude)*p_rad) / 2 + cos(p1.latitude * p_rad) * cos(p2.latitude * p_rad) * (1-cos((p2.longitude - p1.longitude)*p_rad))/2
    return int((12742 * asin(sqrt(a))) * km_to_nm)

def sog_time_distance(p1, p2):
    time_elapsed = p2.timestamp - p1.timestamp
    nautical_miles_sailed = float(p1.sog * ((time_elapsed.total_seconds() / 60) / 60))
    return int(nautical_miles_sailed)

# Logging for file
def get_logger():
    Log_Format = "[%(levelname)s] -  %(asctime)s - %(message)s"
    logging.basicConfig(format = Log_Format,
                        force = True,
                        handlers = [
                            logging.FileHandler(ERROR_LOG_FILE_PATH),
                            logging.StreamHandler()
                        ],
                        level = logging.INFO)

    logger = logging.getLogger()
    return logger

def get_data_from_query(sql_query):
    db_string = f"postgresql://{USER}:{PASS}@{HOST_DB}/{DB_NAME}"
    engine = create_engine(db_string)

    sql = psql.read_sql_query(sql=sql_query, con=engine)
    dataframe = pd.DataFrame(sql)

    return dataframe

def get_trips(df):
    trip_list = {}
    i = 0
    for mmsi in df.mmsi.drop_duplicates():
        trip = Trip(mmsi)
        trip_list[mmsi] = trip
        
    for mmsi, latitude, longitude, sog, timestamp in zip(df.mmsi, df.latitude, df.longitude, df.sog, df.timestamp):
        i+=1
        if(i % 100000 == 0):
            print(f"Added {i} points so far...")
        try:
            trip = trip_list.get(mmsi)
            trip.add_point_to_trip(Point(longitude,latitude,sog,mmsi,timestamp))
        except Exception as e:
            logger.critical(f"Could not access index/mmsi {mmsi} in trip_list array.")
            print(f"Length of triplist: {len(trip_list)}")
            quit()

    return trip_list

def partition_trips(trip_list):
    print(f"BEfore partiton: {len(trip_list)}")
    total_trips_cleansed = []
    trips_removed = 0

    # Compare distances between each point in each trip
    for trip_key in trip_list.copy():
        trip = trip_list[trip_key]
        points_in_trip = trip.get_points_in_trip()

        if(len(points_in_trip) < MINIMUM_POINTS_IN_TRIP):
            trip_list.pop(trip_key)
            logger.info(f"Removed trip from {trip.get_mmsi()} as it only has {len(points_in_trip)} points.")
            trips_removed += 1
            continue

        # Cutting points used when splitting trips into multiple trips
        curr_point = points_in_trip[0]
        cut_point = points_in_trip[0]

        # Used for counting number of points below the threshold
        index = 0

        # Used to define if we are going to split into a new trip
        is_new_trip = False
        
        # Used to keep track of how far a ship has travelled when a new trip is being made
        # Basically, if a ship is at a still-stand (e.g., in harbor or at anker) we wait untill the ship has sailed
        # at least MAX_DIST_IN_HARBOR before we consider it a new trip (so we don't get multiple trips while the ship is still at port/standstill)
        dist_to_new_trip = 0

        # In case a trip hasn't been split, we still need to include the original trip
        # in our final list of trips (total_trips_cleansed)
        route_has_been_cut = False

        # Temp list to hold points that is below a given threshold
        points_below_threshold = []

        # Skip the first iteration, as that is assigned to curr_point
        for point in points_in_trip[1:]:
            # Add points in which they have a speed below the maximum allowed speed in danish harbors
            # We want MAX_SPEED_IN_HARBOR points in sequence to be below the threshold, before we consider a ship 'stopped'
            if (point.get_sog() < MAX_SPEED_IN_HARBOR):
                points_below_threshold.append(point)
                index += 1
            else:
                points_below_threshold.clear()
                index = 0
            
            # If we achieve the amount of points in our cut off, we calculate the distance between the first and last point
            # And the time difference between them. If more than MIN_TIME minutes has passed, and it has sailed less MAX_DIST
            # We define it as a new trip
            if(index == MAX_POINTS_IN_HARBOR):
                dist_p1_p20 = lat_long_distance(points_below_threshold[0], points_below_threshold[MAX_POINTS_IN_HARBOR - 1])
                time_diff = abs((points_below_threshold[0].get_timestamp() - points_below_threshold[-1].get_timestamp()).total_seconds()/60)

                if(dist_p1_p20 <= MAX_DIST and time_diff >= MIN_TIME):
                    is_new_trip = True
                else:
                    is_new_trip = False
                    points_below_threshold = []
                    index = 0
            
            if(is_new_trip):
                dist_to_new_trip += lat_long_distance(curr_point, point)
        
            # If the ship has exceeded our distance cut-off for when a new trip begin
            # we make the trip, and add the points to it by using the cut_point and curr_point.
            if(dist_to_new_trip >= MAX_DIST_IN_HARBOR):
                new_trip = Trip(curr_point.get_mmsi())

                index_cut = points_in_trip.index(cut_point)
                index_curr = points_in_trip.index(curr_point)

                new_trip.insert_point_list(points_in_trip[index_cut:index_curr])

                # Update our cut points for a (potential) new trip later
                cut_point = curr_point
                total_trips_cleansed.append(new_trip)
            
                # Reset our distance and new trip variables (as there can be several trips)
                dist_to_new_trip = 0
                is_new_trip = False
                route_has_been_cut = True

            # Update our current point
            curr_point = point

        # If we haven't split a route into several routes, we append it to our cleansed routes and then pop it
        # Else, just pop (saves memory)
        if(not route_has_been_cut):
            total_trips_cleansed.append(trip)

        trip_list.pop(trip_key)
    
    trip_list = total_trips_cleansed

    print(f"After partiton: {len(trip_list)}")
    
    return trip_list

def remove_outliers(trip_list):
    logger.info(f"Removing unrealistic points for all trips")
    for trip in trip_list:
        points_in_trip = trip.get_points_in_trip()
        curr_point = points_in_trip[0]

        if(len(points_in_trip) < MINIMUM_POINTS_IN_TRIP):
            trip_list.remove(trip)
            continue

        for point in points_in_trip[1:]:
            lat_long = lat_long_distance(curr_point, point)
            time_sog = sog_time_distance(curr_point, point)
            diff = abs(lat_long - time_sog)

            if(diff > 10):
                trip.remove_point_from_trip(point)
            else:
                curr_point = point

    for trip in trip_list:
        if(len(trip.get_points_in_trip()) < MINIMUM_POINTS_IN_TRIP):
            trip_list.remove(trip)
            
    print(f"len of trip_list: {len(trip_list)}")
    return trip_list

def export_trips_csv(trip_list, CSV_PATH = CSV_PATH):
    logger.info("Exporting trips to csv..")
    header = ['mmsi','latitude','longitude','timestamp']
    
    with open(CSV_PATH + 'routes.csv', 'w', encoding='UTF-8', newline='') as f:
        writer = csv.writer(f)

        #Write header:
        writer.writerow(header)

        #Write data:
        for trip in trip_list:
            for point in trip.get_points_in_trip():
                row = [point.get_mmsi(), point.latitude, point.longitude, point.get_timestamp()]
                writer.writerow(row)


logger = get_logger()

def get_cleansed_data():
    sql_query = "SELECT * " \
                "FROM raw_data " \
                "WHERE "\
                    "(mobile_type = 'Class A') AND "\
                    "(latitude >= 53.5 AND latitude <= 58.5) AND "\
                    "(longitude >= 3.2 AND longitude <= 16.5) AND "\
                    "(sog >= 0 AND sog <= 102) AND " \
                    "(mmsi IS NOT NULL) " \
                    "ORDER BY timestamp ASC "
    df = get_data_from_query(sql_query)
    trip_list = partition_trips(df)
    trip_list = remove_outliers(trip_list)

    return trip_list
