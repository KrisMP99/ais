from venv import create
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString
from dotenv import load_dotenv
from time import time
import data_cleansing as dc
import psycopg2
import os
from sqlalchemy import create_engine
from geoalchemy2 import Geometry


USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
HOST_DB = os.getenv('HOST_DB')
DB_NAME = os.getenv('DB_NAME')

if __name__ == '__main__':
    # Loading of the point data from the csv file
    # df = pd.read_csv('C:/Users/alexf/PycharmProjects/pythonProject/routes.csv')
    df = dc.get_data_from_query("SELECT * " \
            "FROM raw_data " \
            "WHERE "\
                "(mobile_type = 'Class A') AND "\
                "(latitude >= 53.5 AND latitude <= 58.5) AND "\
                "(longitude >= 3.2 AND longitude <= 16.5) AND "\
                "(sog >= 0 AND sog <= 102) AND " \
                "(mmsi IS NOT NULL) " \
                "ORDER BY timestamp ASC ")

    trip_list = dc.get_trips(df)

    trip_list = dc.partition_trips(trip_list)

    trip_list = dc.remove_outliers(trip_list)

    mmsi_line = []

    conn = None
    cursor = None

    try:
        conn = psycopg2.connect(database="aisdb", user=USER, password=PASS, host="localhost", port="5432")
        cursor = conn.cursor()
    except(Exception, psycopg2.DatabaseError) as err:
        print(err)

    for trip in trip_list: 
        pointList = trip.get_points_in_trip()
        data = []
        for point in pointList:
            data.append([point.latitude, point.longitude])
        
        df = pd.DataFrame(data, columns=['latitude','longitude'])
        
        coordinates = df[["latitude", "longitude"]].values

        line = LineString(coordinates)

        tolerance = 0.0015

        simplified_line = line.simplify(tolerance, preserve_topology=False)

        mmsi_line.append([trip.get_mmsi(), simplified_line])

        x_y_coords = simplified_line.xy

        points_in_trip = trip.get_points_in_trip()
        timestamp = 0

        # Make trip in database
        trip_sql = f"INSERT INTO trips(mmsi) VALUES ({trip.get_mmsi()}) RETURNING trip_id"
        cursor.execute(trip_sql)
        trip_id = cursor.fetchone()[0]

        for x, y in zip(x_y_coords[0], x_y_coords[1]):
            for point in points_in_trip:
                if x == point.latitude and y == point.longitude:
                    timestamp = point.timestamp
                    break
            
            sql = f"INSERT INTO points(trip_id, mmsi, timestamp, point) VALUES({trip_id}, {trip.get_mmsi()}, '{timestamp}', ST_SetSRID(ST_MakePoint({x}, {y}), 3857))"
            cursor.execute(sql)
        
            
        

    conn.commit()
    cursor.close()
    conn.close()

        # print(line.length, 'line length')
        # print(simplified_line.length, 'simplified line length')
        # print(len(line.coords), 'coordinate pairs in full data set')
        # print(len(simplified_line.coords), 'coordinate pairs in simplified data set')
        # print(round(((1 - float(len(simplified_line.coords)) / float(len(line.coords))) * 100), 1), 'percent compressed')
        

        # lon = pd.Series(pd.Series(simplified_line.coords.xy)[1])
        # lat = pd.Series(pd.Series(simplified_line.coords.xy)[0])
        # si = pd.DataFrame({'latitude': lat, 'longitude': lon})
        # si.tail()
        # si.to_csv('newCSVFile')
        # print(si)
    



# https://geoffboeing.com/2014/08/reducing-spatial-data-set-size-with-douglas-peucker/
# https://github.com/gboeing/2014-summer-travels
# https://www.convertcsv.com/csv-to-json.htm