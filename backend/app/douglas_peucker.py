from venv import create
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString
import data_cleansing as dc

if __name__ == '__main__':

    COLUMNS = ['timestamp', 'type_of_mobile', 'mmsi', 'latitude', 'longitude', 'navigational_status', 'rot', 'sog', 'cog', 'heading', 'imo', 'callsign', 'name', 'ship_type', 'width', 'length', 'type_of_position_device', 'draught', 'destination', 'trip']

    # Loading of the point data from the csv file
    trip_list = dc.get_cleansed_data()
    mmsi_line = []

    all_points = []
    trip_index = 0

    for trip in trip_list: 
        point_list = trip.get_points_in_trip()
        trip_point = []
        new_trip = []
        for p in point_list:
            trip_point.append([p.latitude, p.longitude])
        
        df = pd.DataFrame(trip_point, columns=['latitude','longitude'])
        
        coordinates = df[["latitude", "longitude"]].values

        line = LineString(coordinates)

        tolerance = 0.0015

        simplified_line = line.simplify(tolerance, preserve_topology=False)

        mmsi_line.append([trip.get_mmsi(), simplified_line])

        x_y_coords = simplified_line.xy

        points_in_trip = trip.get_points_in_trip()
        timestamp = 0
        
        # Make trip in database
        # trip_sql = f"INSERT INTO trips(mmsi) VALUES ({trip.get_mmsi()}) RETURNING trip_id"
        # cursor.execute(trip_sql)
        # trip_id = cursor.fetchone()[0]

        
        for x, y in zip(x_y_coords[0], x_y_coords[1]):
            for p in points_in_trip:
                if x == p.latitude and y == p.longitude:
                    new_trip.append([p.timestamp, p.type_of_mobile, p.mmsi, p.latitude, p.longitude, p.navigational_status, p.rot, p.sog, p.cog, p.heading, p.imo, p.callsign, p.name, p.ship_type, p.width, p.length, p.type_of_position_device, p.draught, p.destination, trip_index])
        
        if(len(new_trip) > 10):
            all_points.append(new_trip[0])
            trip_index += 1    

    df = pd.DataFrame(all_points, columns=COLUMNS)
    print(df.to_string())
    
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
    



# https://geoffboeing.com/2014/08/reducing-spatial-data-set-size-with-douglas-peucker/
# https://github.com/gboeing/2014-summer-travels
# https://www.convertcsv.com/csv-to-json.htm