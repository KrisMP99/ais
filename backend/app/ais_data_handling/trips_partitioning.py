import os
from dotenv import load_dotenv
from numpy import NaN
import pandas as pd
import geopandas as gpd
import pandas.io.sql as psql
from sqlalchemy import create_engine
import csv
from shapely.geometry import Point
import numpy as np

COLUMNS = ['timestamp', 'type_of_mobile', 'mmsi', 'navigational_status', 'rot', 'sog', 'cog', 'heading', 'imo', 'callsign', 'name', 'ship_type', 'width', 'length', 'type_of_position_fixing_device', 'draught', 'destination', 'point', 'trip_id', 'simplified_trip_id']

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
HOST_DB = os.getenv('HOST_DB')
DB_NAME = os.getenv('DB_NAME')
ERROR_LOG_FILE_PATH = os.getenv('ERROR_LOG_FILE_PATH')
CSV_FILES_PATH = os.getenv('CSV_FILES_PATH')

# Thresholds
# Distances are in meters
MAX_SPEED_IN_HARBOR = 1.5
# MAX_POINTS_IN_HARBOR = 50
# MAX_DIST_IN_HARBOR = 2000
MINIMUM_POINTS_IN_TRIP = 100
MAX_DIST = 2000
MIN_TIME = 4

DATA = []

class Trip:
    def __init__(self, mmsi, trip_id = None, simplified_trip_id = None):
        self.mmsi = mmsi
        self.point_list = []
        self.trip_id = trip_id
        self.simplified_trip_id = simplified_trip_id
    
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
    
class PointClass:
    def __init__(self, timestamp, type_of_mobile, mmsi, navigational_status, rot, sog, cog, heading, imo, callsign, name, ship_type, width, length, type_of_position_fixing_device, draught, destination, Point: Point, trip_id=None, simplified_trip_id=None):
        self.timestamp = timestamp 
        self.type_of_mobile = type_of_mobile 
        self.mmsi = mmsi 
        self.navigational_status = navigational_status
        self.rot = rot
        self.sog = sog
        self.cog = cog
        self.heading = heading
        self.imo = imo
        self.callsign = callsign
        self.name = name
        self.ship_type = ship_type
        self.width = width
        self.length = length
        self.type_of_position_fixing_device = type_of_position_fixing_device
        self.draught = draught
        self.destination = destination
        self.trip_id = trip_id
        self.simplified_trip_id = simplified_trip_id
        self.Point = Point

    def get_mmsi(self):
        return self.mmsi

    def get_timestamp(self):
        return self.timestamp
    
    def get_sog(self):
        return self.sog

def sog_time_distance(p1, p2):
    time_elapsed = p2.timestamp - p1.timestamp
    nautical_miles_sailed = float(p1.sog * ((time_elapsed.total_seconds() / 60) / 60))
    return int(nautical_miles_sailed)

def get_data_from_query(sql_query):
    db_string = f"postgresql://{USER}:{PASS}@{HOST_DB}/{DB_NAME}"
    engine = create_engine(db_string)

    with engine.connect() as conn:
        sql = psql.read_sql_query(sql=sql_query, con=conn)
        dataframe = pd.DataFrame(sql)

    return dataframe

def get_trips(df: gpd.GeoDataFrame, logger):
    df = df.sort_values(by="timestamp", ignore_index=True)

    trip_list = {}
    trip_list: list[Trip]
    for mmsi in df['mmsi'].drop_duplicates():
        trip = Trip(mmsi)
        trip_list[mmsi] = trip
    
    for timestamp, type_of_mobile, mmsi, navigational_status, rot, sog, cog, heading, imo, callsign, name, ship_type, width, length, type_of_position_fixing_device, draught, destination, geometry in zip(df.timestamp, df.type_of_mobile, df.mmsi, df.navigational_status, df.rot, df.sog, df.cog, df.heading, df.imo, df.callsign, df.name, df.ship_type, df.width, df.length, df.type_of_position_fixing_device, df.draught, df.destination, df.geometry):
        try:
            trip = trip_list.get(mmsi)
            trip: Trip
            trip.add_point_to_trip(PointClass(timestamp, type_of_mobile, mmsi, navigational_status, rot, sog, cog, heading, imo, callsign, name, ship_type, width, length, type_of_position_fixing_device, draught, destination, Point=geometry))
        except Exception as e:
            logger.critical(f"Could not access index/mmsi {mmsi} in trip_list array. Error: {e}")
            quit()

    return trip_list

def partition_trips(trip_list: list[Trip], logger):
    logger.info(f"Before partiton: {len(trip_list)}")

    DATA.append(len(trip_list))

    total_trips_cleansed = []
    trips_removed = 0
    trips_added = 0
    stats_points_in_trip = []

    # Compare distances between each point in each trip
    for trip_key in trip_list.copy():
        trip = trip_list[trip_key]
        trip: Trip
        points_in_trip = trip.get_points_in_trip()
        points_in_trip: list[PointClass]

        stats_points_in_trip.append(len(points_in_trip))

        if(len(points_in_trip) < MINIMUM_POINTS_IN_TRIP):
            trip_list.pop(trip_key)
            trips_removed += 1
            continue

        # Cutting points used when splitting trips into multiple trips
        curr_point = points_in_trip[0]
        cut_point_begin = points_in_trip[0]
        cut_point_end = points_in_trip[0]
        index_cut_begin = 0
        index_cut_end = 0

        # Used for counting number of points below the threshold
        index = 0

        # Used to define if we are going to split into a new trip
        possibly_new_trip = False
        skip = False
        cut_trip = False
        points_left_over = False

        # Temp list to hold points that is below a given threshold
        points_below_threshold = []
        points_below_threshold: list[PointClass]

        # Skip the first iteration, as that is assigned to curr_point
        point: PointClass
        for point in points_in_trip:
            # Add points in which they have a speed below the maximum allowed speed in danish harbors
            # We want MAX_SPEED_IN_HARBOR points in sequence to be below the threshold, before we consider a ship 'stopped'
            if (point.get_sog() < MAX_SPEED_IN_HARBOR):
                if not possibly_new_trip:
                    cut_point_end = point
                
                points_below_threshold.append(point)
                index += 1
                possibly_new_trip = True
                skip = True
            else:
                skip = False
                index = 0
            
            # If we achieve the amount of points in our cut off, we calculate the distance between the first and last point
            # And the time difference between them. If more than MIN_TIME minutes has passed, and it has sailed less MAX_DIST
            # We define it as a new trip
            if(possibly_new_trip and not skip):
                # dist_p1_p20 = points_below_threshold[0].Point.distance(points_below_threshold[MAX_POINTS_IN_HARBOR - 1].Point)
                time_diff = abs((points_below_threshold[0].get_timestamp() - points_below_threshold[-1].get_timestamp()).total_seconds()/60)
                possibly_new_trip = False

                if(time_diff >= MIN_TIME):
                    cut_trip = True
                    points_left_over = False
                else:
                    points_left_over = True
                    possibly_new_trip = False
                    points_below_threshold.clear()
                    index = 0
        
            # If the ship has exceeded our distance cut-off for when a new trip begin
            # we make the trip, and add the points to it by using the cut_point and curr_point.
            if(cut_trip):
                trips_added += 1
                new_trip = Trip(point.get_mmsi())

                index_cut_begin = points_in_trip.index(cut_point_begin)
                index_cut_end = points_in_trip.index(cut_point_end)

                new_trip.insert_point_list(points_in_trip[index_cut_begin:index_cut_end])

                # Update our cut points for a (potential) new trip later
                cut_point_begin = point
                cut_point_end = point
                total_trips_cleansed.append(new_trip)
            
                # Reset our distance and new trip variables (as there can be several trips)
                cut_trip = False
                skip = False
                possibly_new_trip = False
                points_below_threshold.clear()

            # Update our current point (might not be needed anymore?)
            curr_point = point

        # If cut_point != curr_point after going through all the points,
        # means that there are still a sub trip left in the original trip
        # Example: 
        # The vertical lines | represents a cut point.
        # ----|----|-----|-----
        # A new trip would then be cut, containing the points inside the '[]'
        # [----]|[----]|[-----]|-----
        # As seen in the example, we also need the last part.
        if index_cut_begin == 0 and index_cut_end == 0 and not possibly_new_trip:
            total_trips_cleansed.append(trip)
        elif index_cut_end != (len(points_in_trip) - 1) and (points_left_over or not skip):
            new_trip = Trip(curr_point.get_mmsi())
            new_trip.insert_point_list(points_in_trip[index_cut_begin:-1])
            total_trips_cleansed.append(new_trip)

        # Remove the trip we just went trough (saves memory)
        # trip_list.pop(trip_key)  <--- can this be done safely?

    logger.info(f"Removed {trips_removed} trips as they had less than {MINIMUM_POINTS_IN_TRIP} points, and added {trips_added} new trips from splitting.")
    trip_list = total_trips_cleansed

    
    DATA.append(np.mean(stats_points_in_trip))
    DATA.append(np.median(stats_points_in_trip))
    DATA.append(trips_removed)
    DATA.append(trips_added)

    print(f"After partiton: {len(trip_list)}")
    
    return trip_list

def remove_outliers(trip_list: list[Trip], logger):
    logger.info(f"Removing unrealistic points for all trips")
    trips_outliers_removed = []

    stats_points_len = []
    outliers_removed = []

    for trip in trip_list:
        points_in_trip = trip.get_points_in_trip()
        stats_points_len.append(len(points_in_trip))
        if(len(points_in_trip) > MINIMUM_POINTS_IN_TRIP):
            trips_outliers_removed.append(trip)
    
    DATA.append(np.mean(stats_points_len))
    DATA.append(np.median(stats_points_len))
    DATA.append(len(trip_list) - len(trips_outliers_removed))

    trip_list = trips_outliers_removed

    for trip in trip_list:
        temp = 0
        points_in_trip = trip.get_points_in_trip()
        curr_point = points_in_trip[0]
        
        point: PointClass
        for point in points_in_trip[1:]:
            lat_long = curr_point.Point.distance(point.Point)
            time_sog = sog_time_distance(curr_point, point)
            diff = abs(lat_long - time_sog)

            if(diff > MAX_DIST):
                trip.remove_point_from_trip(point)
                temp += 1
            else:
                curr_point = point
        outliers_removed.append(temp)
    
    DATA.append(np.sum(outliers_removed))
    DATA.append(np.average(outliers_removed))

    # This might not work correctly, remember to revisit
    trips_outliers_removed_second = []
    trip: Trip
    for trip in trip_list:
        if(len(trip.get_points_in_trip()) > MINIMUM_POINTS_IN_TRIP):
            trips_outliers_removed_second.append(trip)

    DATA.append(len(trip_list) - len(trips_outliers_removed_second))
    trip_list = trips_outliers_removed_second
    logger.info(f"Removed unrealistic points for all trips. Adding trips keys")
    print(f"len of trip_list: {len(trip_list)}")

    # Add the trip_id index for each trip
    sql = "SELECT MAX(trip_dim.trip_id) as trip_id, MAX(simplified_trip_dim.simplified_trip_id) as simplified_id FROM trip_dim, simplified_trip_dim"
    df = get_data_from_query(sql)
    trip_PK_key = df['trip_id'].values[0]
    simplified_trip_PK_key = df['simplified_id'].values[0]

    if trip_PK_key is None:
        trip_PK_key = 0
    if simplified_trip_PK_key is None:
        simplified_trip_PK_key = 0

    # add trip_ids and convert to dataframe
    point_list = []
    trip: Trip
    for trip in trip_list:
        trip_PK_key += 1
        simplified_trip_PK_key += 1
        trip.trip_id = trip_PK_key
        trip.simplified_trip_id = None

        p: PointClass
        for p in trip.get_points_in_trip():
            p.trip_id = trip.trip_id
            p.simplified_trip_id = None
            point_list.append([p.timestamp, p.type_of_mobile, p.mmsi, p.navigational_status, p.rot, p.sog, p.cog, p.heading, p.imo, p.callsign, p.name, p.ship_type, p.width, p.length, p.type_of_position_fixing_device, p.draught, p.destination, p.Point, p.trip_id, p.simplified_trip_id])
    
    logger.info(f"Done adding trip keys. Converting to geopandas dataframe.")
    df = pd.DataFrame(point_list, columns=COLUMNS)
    df = gpd.GeoDataFrame(df, geometry=df['point'], crs="EPSG:3857")
    return df

def export_trips_csv(trip_list: list[Trip], logger, CSV_PATH = CSV_FILES_PATH):
    logger.info("Exporting trips to csv..")
    header = ['mmsi','latitude','longitude','timestamp']
    
    with open(CSV_PATH + 'routes.csv', 'w', encoding='UTF-8', newline='') as f:
        writer = csv.writer(f)

        #Write header:
        writer.writerow(header)

        #Write data:a
        point: PointClass
        for trip in trip_list:
            for point in trip.get_points_in_trip():
                row = [point.get_mmsi(), point.latitude, point.longitude, point.get_timestamp()]
                writer.writerow(row)

def get_cleansed_data(df: gpd.GeoDataFrame, logger, file_name: str) -> gpd.GeoDataFrame:
    DATA.clear()
    DATA.append(file_name)
    trip_list = get_trips(df, logger)
    trip_list = partition_trips(trip_list, logger)
    trip_list = remove_outliers(trip_list, logger)

    HEADER = [file_name, 'trips_before_partitioning', 'avg_points_in_trip_before', 
              'median_points_in_trip_before', 'number_of_trips_removed', 'new_trips_added', 
              'avg_points_in_trip_after', 'median_points_in_trip_after', 'number_of_trips_removed_2',
              'outliers_total_removed', 'outliers_avg_removed_per_trip','number_of_trips_removed_3',
              'max_speed_in_harbor', 'minimum_points_in_trip',
              'max_dist', 'min_time'
               ]

    DATA.append(MAX_SPEED_IN_HARBOR)
    DATA.append(MINIMUM_POINTS_IN_TRIP)
    
    with open(CSV_FILES_PATH + file_name + '_stats_2.csv', 'w', encoding="UTF8", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerow(DATA)
    
    DATA.clear()

    return trip_list



'''
- Number of rows before any cleansing at all
- Number of rows after removing:
    - Class B ship types
    - Rows with NULL in MMSI
    - Rows with NULL in timestamp
    - Lat,long outside our area of interest
    - 0.1 <= SOG <= 102
- Number of trips before trip partitioning
- Average number of points in each trip before trip partitioning
    - and median?

- Number of trips removed before trip partitioning (points < 500)
- Number of new trips added from trips partitioning
- Number of trips removed after trips partitioning (points < 500)
- Total number of points removed from each trip after trips partitioning ((dist(p1,p2) - time_dist(p1,p2)) > 2km)
    - (and avg)
- Number of trips removed after point removal (points < 500)
    - (Total number of trips after partitioning)
- Total time taken for the csv file
- Total time taken for inserting into database
- Total time taken for rounding coordinates, generating line strings, adding hex/square ids, vacuuming and analyzing
- Points before and after line simplification (Douglas Peucker) (total numbers and in percent)
- Query time taken to fetch data for front end
- Total time from clicking 'get trips' on front end until stuff is displayed


'''