import os
import logging
from dotenv import load_dotenv
import pandas as pd
import pandas.io.sql as psql
from sqlalchemy import create_engine
from math import cos, asin, sqrt
import csv

COLUMNS = ['timestamp', 'mobile_type', 'mmsi', 'latitude', 'longitude', 'navigational_status', 'rot', 'sog', 'cog', 'heading', 'imo', 'callsign', 'name', 'ship_type', 'cargo_type', 'width', 'length', 'type_of_position_fixing_device', 'draught', 'destination', 'eta', 'data_source_type']

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
    def lat_long_distance(self, p):
        km_to_nm = 0.53
        p_rad = 0.017        # pi / 180
        a = 0.5 - cos((p.latitude - self.latitude)*p_rad) / 2 + cos(self.latitude * p_rad) * cos(p.latitude * p_rad) * (1-cos((p.longitude - self.longitude)*p_rad))/2
        return int((12742 * asin(sqrt(a))) * km_to_nm)
    
    def sog_time_distance(self, p):
        time_elapsed = p.timestamp - self.timestamp
        nautical_miles_sailed = float(self.sog * ((time_elapsed.total_seconds() / 60) / 60))
        return int(nautical_miles_sailed)



# establish connection to database
logger = get_logger()

db_string = f"postgresql://{USER}:{PASS}@{HOST_DB}/{DB_NAME}"
engine = create_engine(db_string)


sql_query = "SELECT " \
            "timestamp, mobile_type, mmsi, latitude, longitude, navigational_status, rot, sog, cog, heading, imo, callsign, name, ship_type, cargo_type, width, length, type_of_position_fixing_device, draught, destination, eta, data_source_type " \
            "FROM raw_data " \
            "WHERE "\
                "(mobile_type = 'Class A') AND "\
                "(latitude >= 53.5 AND latitude <= 58.5) AND "\
                "(longitude >= 3.2 AND longitude <= 16.5) AND "\
                "(sog >= 0 AND sog <= 102) AND " \
                "(mmsi IS NOT NULL) " \
                "ORDER BY timestamp ASC "

            
sql = psql.read_sql_query(sql=sql_query, con=engine)
df = pd.DataFrame(sql, columns=COLUMNS)

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

num_of_trips_beginning = len(trip_list)

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
            points_below_threshold = []
            index = 0
        
        # If we achieve the amount of points in our cut off, we calculate the distance between the first and last point
        # And the time difference between them. If more than MIN_TIME minutes has passed, and it has sailed less MAX_DIST
        # We define it as a new trip
        if(index == MAX_POINTS_IN_HARBOR):
            dist_p1_p20 = points_below_threshold[0].lat_long_distance(points_below_threshold[MAX_POINTS_IN_HARBOR - 1])
            time_diff = abs((points_below_threshold[0].get_timestamp() - points_below_threshold[-1].get_timestamp()).total_seconds()/60)

            if(dist_p1_p20 <= MAX_DIST and time_diff >= MIN_TIME):
                is_new_trip = True
            else:
                is_new_trip = False
                points_below_threshold = []
                index = 0
        
        if(is_new_trip):
            dist_to_new_trip += curr_point.lat_long_distance(point)
    
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

num_trips_new = len(total_trips_cleansed)

logger.info(f"Removing unrealistic points for all trips")

for trip in total_trips_cleansed:
    points_in_trip = trip.get_points_in_trip()
    curr_point = points_in_trip[0]

    if(len(points_in_trip) < MINIMUM_POINTS_IN_TRIP):
        total_trips_cleansed.remove(trip)
        continue

    for point in points_in_trip[1:]:
        lat_long = curr_point.lat_long_distance(point)
        time_sog = curr_point.sog_time_distance(point)
        diff = abs(lat_long - time_sog)

        if(diff > 10):
            trip.remove_point_from_trip(point)
        else:
            curr_point = point

trips_removed_2 = 0
for trip in total_trips_cleansed:
    if(len(trip.get_points_in_trip()) < MINIMUM_POINTS_IN_TRIP):
        trips_removed_2 +=1
        total_trips_cleansed.remove(trip)


num_trips_final = len(total_trips_cleansed)


logger.info(f"Total trips removed from not having enough points: {trips_removed}")

logger.info(f"Number of trips before trip partitioning {num_of_trips_beginning}")
logger.info(f"Number of trips after trip partitioning: {num_trips_new}")

logger.info(f"Removed {trips_removed_2} unrealistic points from trips")

logger.info(f"After ALL cleansing, we have {num_trips_final} trips.")

logger.info("Exporting trips to csv..")

header = ['mmsi','latitude','longitude','timestamp']

with open(CSV_PATH + 'routes.csv', 'w', encoding='UTF-8', newline='') as f:
    writer = csv.writer(f)

    #Write header:
    writer.writerow(header)

    #Write data:
    for trip in total_trips_cleansed:
        for point in trip.get_points_in_trip():
            row = [point.get_mmsi(), point.latitude, point.longitude, point.get_timestamp()]
            writer.writerow(row)