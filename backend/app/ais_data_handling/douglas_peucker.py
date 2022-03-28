from venv import create
import pandas as pd
from shapely.geometry import LineString, Point
import geopandas as gpd
import datetime
from pandarallel import pandarallel
import warnings
from shapely.errors import ShapelyDeprecationWarning
warnings.filterwarnings("ignore", category=ShapelyDeprecationWarning) 


def convert_to_point(df):
    df['geometry'] = Point(df['latitude'], df['longitude'])

def create_line_strings(point_df, logger):
    # COLUMNS = ['timestamp', 'type_of_mobile', 'mmsi', 'latitude', 'longitude', 'navigational_status', 'rot', 'sog', 'cog', 'heading', 'imo', 'callsign', 'name', 'ship_type', 'width', 'length', 'type_of_position_fixing_device', 'draught', 'destination', 'trip_id', 'simplified_trip_id']
    pandarallel.initialize(progress_bar=True, verbose=2, use_memory_fs=False)
    
    logger.info("Creating line strings")
    logger.info("Setting precision of lat and long to 4 decimals")
    point_df = point_df.round({'latitude':4,'longitude':4})  # Only 4 decimals on lat and long
    logger.info("Sat precision!")
    time_begin = datetime.datetime.now()
    line_string_df = gpd.GeoDataFrame(point_df, geometry=point_df.parallel_apply(convert_to_point, axis=1))
    logger.info("Finished converting all lat- and longs to points.")
    line_string_df = line_string_df.groupby('trip_id').parallel_apply(lambda x: LineString(x.geometry.tolist()))

    time_end = datetime.datetime.now()
    time_delta = time_end - time_begin
    
    print(line_string_df.head(5))
    print(print(f"Took approx: {time_delta.total_seconds() / 60} minutes, or {time_delta.total_seconds()}"))
    quit()

    # simplified_line_strings_df = point_df.groupby('trip_id').apply(lambda x: x. )
    

    # total_trip_points = []
    # line_strings = []
    # simplified_line_strings = []

    # # mmsi_line = []
    # for trip in trip_list: 
    #     point_list = trip.get_points_in_trip()
    #     trip_point = []

    #     for p in point_list:
    #         trip_point.append([p.latitude, p.longitude])
        
    #     df = pd.DataFrame(trip_point, columns=['latitude','longitude'])
    #     trip_point.clear()
        
    #     coordinates = df[["latitude", "longitude"]].values

    #     line = LineString(coordinates)

    #     tolerance = 0.02

    #     simplified_line = line.simplify(tolerance, preserve_topology=False)


    #     # mmsi_line.append([trip.get_mmsi(), simplified_line])

    #     x_y_coords = simplified_line.xy
        
        
    #     for x, y in zip(x_y_coords[0], x_y_coords[1]):
    #         for p in point_list:
    #             if x == p.latitude and y == p.longitude:
    #                 p.simplified_trip_id = trip.simplified_trip_id
    #                 break

    # for trip in trip_list:
    #     for p in trip.get_points_in_trip():
    #         total_trip_points.append([p.timestamp, p.type_of_mobile, p.mmsi, p.latitude, p.longitude, p.navigational_status, p.rot, p.sog, p.cog, p.heading, p.imo, p.callsign, p.name, p.ship_type, p.width, p.length, p.type_of_position_fixing_device, p.draught, p.destination, p.trip_id, p.simplified_trip_id])

    # df_all_points = pd.DataFrame(total_trip_points, columns=COLUMNS)
    return None

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