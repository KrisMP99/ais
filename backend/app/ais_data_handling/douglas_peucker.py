from venv import create
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString
import trips_partitioning as tp
import data_insertion as di

def create_line_strings():
    COLUMNS = ['timestamp', 'type_of_mobile', 'mmsi', 'latitude', 'longitude', 'navigational_status', 'rot', 'sog', 'cog', 'heading', 'imo', 'callsign', 'name', 'ship_type', 'width', 'length', 'type_of_position_fixing_device', 'draught', 'destination', 'trip_id', 'simplified_trip_id']

    # Loading of the point data from the csv file
    trip_list = tp.get_cleansed_data()
    total_trip_points = []
    mmsi_line = []
    for trip in trip_list: 
        point_list = trip.get_points_in_trip()
        trip_point = []
        for p in point_list:
            trip_point.append([p.latitude, p.longitude])
        
        df = pd.DataFrame(trip_point, columns=['latitude','longitude'])
        trip_point.clear()
        
        coordinates = df[["latitude", "longitude"]].values

        line = LineString(coordinates)

        tolerance = 0.02

        simplified_line = line.simplify(tolerance, preserve_topology=False)

        mmsi_line.append([trip.get_mmsi(), simplified_line])

        x_y_coords = simplified_line.xy
        
        # Make trip in database
        # trip_sql = f"INSERT INTO trips(mmsi) VALUES ({trip.get_mmsi()}) RETURNING trip_id"
        # cursor.execute(trip_sql)
        # trip_id = cursor.fetchone()[0]
        
        for x, y in zip(x_y_coords[0], x_y_coords[1]):
            for p in point_list:
                if x == p.latitude and y == p.longitude:
                    p.simplified_trip_id = trip.simplified_trip_id
                    # total_trip_points.append([p.timestamp, p.type_of_mobile, p.mmsi, p.latitude, p.longitude, p.navigational_status, p.rot, p.sog, p.cog, p.heading, p.imo, p.callsign, p.name, p.ship_type, p.width, p.length, p.type_of_position_fixing_device, p.draught, p.destination, p.trip_id, trip.simplified_trip_id])
                    break

        # for p in point_list:
        #     if p.simplified_trip_id is None:
        #         total_trip_points.append([p.timestamp, p.type_of_mobile, p.mmsi, p.latitude, p.longitude, p.navigational_status, p.rot, p.sog, p.cog, p.heading, p.imo, p.callsign, p.name, p.ship_type, p.width, p.length, p.type_of_position_fixing_device, p.draught, p.destination, p.trip_id, None])

        
    # df['line_string'] = np.nan
    index = 0
    for trip in trip_list:
        #print(f"Currently adding trip {index} in douglas...")
        index +=1
        for p in trip.get_points_in_trip():
            total_trip_points.append([p.timestamp, p.type_of_mobile, p.mmsi, p.latitude, p.longitude, p.navigational_status, p.rot, p.sog, p.cog, p.heading, p.imo, p.callsign, p.name, p.ship_type, p.width, p.length, p.type_of_position_fixing_device, p.draught, p.destination, p.trip_id, p.simplified_trip_id])
        # trip_list.remove(trip)

    df_all_points = pd.DataFrame(total_trip_points, columns=COLUMNS)
    di.insert_into_star(df_all_points)
        # total_trip_points.clear()
        #sql = f"INSERT INTO points(trip_id, mmsi, timestamp, point) VALUES({trip_id}, {trip.get_mmsi()}, '{timestamp}', ST_SetSRID(ST_MakePoint({x}, {y}), 3857))"

        
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
    
create_line_strings()


# https://geoffboeing.com/2014/08/reducing-spatial-data-set-size-with-douglas-peucker/
# https://github.com/gboeing/2014-summer-travels
# https://www.convertcsv.com/csv-to-json.htm