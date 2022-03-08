import os
import logging
from dotenv import load_dotenv
import pandas as pd
import pandas.io.sql as psql
from sqlalchemy import create_engine
from dotenv import load_dotenv

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
    


class Point:
    def __init__(self, longitude, latitude, sog, timestamp):
        self.longitude = longitude
        self.latitude = latitude
        self.sog = sog
        self.timestamp = timestamp
    
    # Manhatten distance because it's fast af
    def distance(self, p):
        return abs((self.longitude - p.longitude) + (self.latitude - p.latitude))

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
                "(latitude >= 54.5 AND latitude <= 58.5) AND "\
                "(longitude >= 3.2 AND longitude <= 16.5) AND "\
                "(heading >= 0 AND heading <= 359) AND "\
                "(rot >=0 AND rot <= 720) AND" \
                "(sog >= 0 AND sog <= 102) AND" \
                "(mmsi IS NOT NULL) " \
                "LIMIT 100000"

            
for sql in psql.read_sql_query(sql=sql_query, con=engine, chunksize=CHUNK_SIZE):
    df = pd.DataFrame(sql, columns=COLUMNS)
    
    #print(df.mmsi.drop_duplicates())
    route_list = []

    # For each unqiue mmsi:
    #   1. Check the other rows, to see if the unique mmsi is equal to the current mmsi
    #   2. If yes, take the lat, long, sog and timestamp from the found point and create an instance of a point class, and set this to current_point
    #   3. Find the next point beloning to the same mmsi, and set this to next_point. 
    #      -> Calculate the distance between the two points, and calulcate using the sog and timestamp, 
    #      -> to see if said point is realistically reachable within that time frame
    #   4. If the point is reachable, keep the point, and set 'next_point' to the 'current_point' and repeat the process, for all points, and all mmsi's. 
    #   5. If the point is unreacable, delete the point, and then take the next point.

    for mmsi_outer in df.mmsi.drop_duplicates():
        route = Route(mmsi_outer)
        print("Created route")
        for mmsi_inner, latitude, longitude, sog, timestamp in zip(df.mmsi, df.latitude, df.longitude, df.sog, df.timestamp):
            if mmsi_outer == mmsi_inner:
                print(f"Found unique mmsi: {mmsi_outer}  -  {mmsi_inner}\nAdding point: {longitude}, {latitude}, {sog}, {timestamp}")
                route.add_point_to_ship_route(Point(longitude,latitude,sog,timestamp))
        route_list.append(route)
    
    print(f"Number of routes: {len(route_list)}")



logger.info("Done!")