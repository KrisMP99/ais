import os
import logging
from dotenv import load_dotenv
import pandas as pd
import pandas.io.sql as psql
from sqlalchemy import create_engine
from dotenv import load_dotenv
from math import cos, asin, sqrt, pi
import datetime
import math

COLUMNS = ['timestamp', 'mobile_type', 'mmsi', 'latitude', 'longitude', 'navigational_status', 'rot', 'sog', 'cog', 'heading', 'imo', 'callsign', 'name', 'ship_type', 'cargo_type', 'width', 'length', 'type_of_position_fixing_device', 'draught', 'destination', 'eta', 'data_source_type']

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
HOST_DB = os.getenv('HOST_DB')
DB_NAME = os.getenv('DB_NAME')
ERROR_LOG_FILE_PATH = os.getenv('ERROR_LOG_FILE_PATH')

# chunk size to load in (we do not have enough memory to load in everything at once)
CHUNK_SIZE = 1000000

class Route:
    def __init__(self, mmsi):
        self.mmsi = mmsi
        self.point_list = []
    
    def add_point_to_ship_route(self, point):
        self.point_list.append(point)
    
    def get_points_in_route_list(self):
        return self.point_list
    
    def remove_point_from_route(self, point):
        self.point_list.remove(point)
    
    def get_mmsi(self):
        return self.mmsi
    

class Point:
    def __init__(self, longitude, latitude, sog, timestamp):
        self.longitude = longitude
        self.latitude = latitude
        self.sog = sog
        self.timestamp = timestamp
    
    def get_timestamp(self):
        return self.timestamp
    
    # https://stackoverflow.com/questions/27928/calculate-distance-between-two-latitude-longitude-points-haversine-formula
    def lat_long_distance(self, p):
        km_to_nm = 0.53
        p_rad = 0.017        # pi / 180
        a = 0.5 - cos((p.latitude - self.latitude)*p_rad) / 2 + cos(self.latitude * p_rad) * cos(p.latitude * p_rad) * (1-cos((p.longitude - self.longitude)*p_rad))/2
        return int((12742 * asin(sqrt(a))) * km_to_nm)
    
    def sog_time_distance(self, p):
        #print(f"Point1: {self.latitude}, {self.longitude} - {self.sog} - {self.timestamp}")
        #print(f"Point2: {p.latitude}, {p.longitude} - {p.sog} - {p.timestamp}")
        time_elapsed = p.timestamp - self.timestamp
        nautical_miles_sailed = float(self.sog * ((time_elapsed.total_seconds() / 60) / 60))
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
                "(heading >= 0 AND heading <= 359) AND "\
                "((rot >=0 AND rot <= 720) or rot is null) AND" \
                "((sog >= 0 AND sog <= 102) or sog is null) AND" \
                "(mmsi IS NOT NULL) " \
                "ORDER BY timestamp ASC "

            
sql = psql.read_sql_query(sql=sql_query, con=engine)
df = pd.DataFrame(sql, columns=COLUMNS)

# For each unqiue mmsi:
#   1. Check the other rows, to see if the unique mmsi is equal to the current mmsi
#   2. If yes, take the lat, long, sog and timestamp from the found point and create an instance of a point class, and set this to current_point
#   3. Find the next point beloning to the same mmsi, and set this to next_point. 
#      -> Calculate the distance between the two points, and calulcate using the sog and timestamp, 
#      -> to see if said point is realistically reachable within that time frame
#   4. If the point is reachable, keep the point, and set 'next_point' to the 'current_point' and repeat the process, for all points, and all mmsi's. 
#   5. If the point is unreacable, delete the point, and then take the next point.

route_list = []

n = 0
for mmsi_outer in df.mmsi.drop_duplicates():
    should_add_route = True
    route = Route(mmsi_outer)
    n+=1
    
    for mmsi_inner, latitude, longitude, sog, timestamp in zip(df.mmsi, df.latitude, df.longitude, df.sog, df.timestamp):
        if mmsi_outer == mmsi_inner:
            if math.isnan(latitude) or math.isnan(longitude) or math.isnan(sog) or not isinstance(timestamp, datetime.datetime):
                should_add_route = False
                n -= 1
                break
            route.add_point_to_ship_route(Point(longitude,latitude,sog,timestamp))

    if(should_add_route):
        print(f"Created route {n}")     
        route_list.append(route)

# Compare distances between each point in each route
for route in route_list:
    points_in_route = route.get_points_in_route_list()    
    curr_point = points_in_route[0]

    for point in points_in_route[1:]:
        lat_long = curr_point.lat_long_distance(point)
        time_sog = curr_point.sog_time_distance(point)
        diff = abs(lat_long - time_sog)

        if(diff > 50):
            logger.info(f"Removed point from route, diff is: {diff}")
            logger.info(f"curr_point: lat: {curr_point.latitude} long: {curr_point.longitude} time: {curr_point.timestamp} point2: lat: {point.latitude} long: {point.longitude} time: {point.timestamp}")
            logger.info(f"Removed a point from vessel with mmsi: {route.get_mmsi()} point timestamp {point.get_timestamp()}")
            route.remove_point_from_route(point)
        else:
            curr_point = point

print(f"Number of routes: {len(route_list)}")



logger.info("Done!")