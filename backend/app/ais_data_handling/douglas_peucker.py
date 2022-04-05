
from venv import create
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Point
from trips_partitioning import get_data_from_query

COLUMNS = ['timestamp', 'type_of_mobile', 'mmsi','latitude','longitude', 'navigational_status', 'rot', 'sog', 'cog', 'heading', 'imo', 'callsign', 'name', 'ship_type', 'width', 'length', 'type_of_position_fixing_device', 'draught', 'destination', 'trip_id', 'simplified_trip_id']

# Tolerance for Douglas Peucker algorithm
TOLERANCE = 1000

def create_trip_line_strings(df: gpd.GeoDataFrame, logger) -> gpd.GeoDataFrame:
    logger.info("Creating line strings for trip_dim...")
    trip_df = df.groupby(by=['trip_id'])['geometry'].apply(lambda x: LineString(x.tolist()))
    trip_df = gpd.GeoDataFrame({'trip_id':trip_df.index, 'line_string':trip_df.values}, geometry='line_string', crs="EPSG:3857").set_index('trip_id')
    return trip_df

def create_simplified_trip_line_strings(df: gpd.GeoDataFrame, logger) -> gpd.GeoDataFrame:
    sql = "SELECT MAX(simplified_trip_dim.simplified_trip_id) FROM simplified_trip_dim"
    keys_df = get_data_from_query(sql)
    simplified_trip_PK_key = keys_df['max'].values[0]

    if simplified_trip_PK_key is None:
        simplified_trip_PK_key = 0
    else:
        simplified_trip_PK_key += 1

    logger.info("Creating line strings for simplified trip dim")
    simplified_trip_df = df.groupby(by=['trip_id'])['geometry'].apply(lambda x: LineString(x.tolist()).simplify(tolerance=TOLERANCE,preserve_topology=False))
    simplified_trip_df = gpd.GeoDataFrame({'line_string':simplified_trip_df.values}, geometry='line_string', crs="EPSG:3857")
    simplified_trip_df.insert(0,'simplified_trip_id',range(simplified_trip_PK_key, simplified_trip_PK_key + len(simplified_trip_df)))
    simplified_trip_df = simplified_trip_df.set_index('simplified_trip_id')
    return simplified_trip_df


def test(row, df: gpd.GeoDataFrame):
    result = df.contains(row['geometry'])
    result = result.to_numpy()
    for i, result in enumerate(result):
        if result:
            return df.index.values[i]
    return None
    
def add_simplified_trip_ids(df: gpd.GeoDataFrame, simplified_trip_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    df['simplified_trip_id'] = df.apply(lambda x: test(row=x, df=simplified_trip_df), axis=1)
    return df

# def create_line_strings(trip_list: gpd.GeoDataFrame, logger):    

#     total_trip_points = []

#     # mmsi_line = []
#     for trip in trip_list: 
#         point_list = trip.get_points_in_trip()
#         trip_point = []

#         for p in point_list:
#             trip_point.append([p.latitude, p.longitude])
        
#         df = pd.DataFrame(trip_point, columns=['latitude','longitude'])
#         trip_point.clear()
        
#         coordinates = df[["latitude", "longitude"]].values

#         line = LineString(coordinates)

#         tolerance = 0.02

#         simplified_line = line.simplify(tolerance, preserve_topology=False)


#         # mmsi_line.append([trip.get_mmsi(), simplified_line])

#         x_y_coords = simplified_line.xy
        
        
#         for x, y in zip(x_y_coords[0], x_y_coords[1]):
#             for p in point_list:
#                 if x == p.latitude and y == p.longitude:
#                     p.simplified_trip_id = trip.simplified_trip_id
#                     break

#     for trip in trip_list:
#         for p in trip.get_points_in_trip():
#             total_trip_points.append([p.timestamp, p.type_of_mobile, p.mmsi, p.latitude, p.longitude, p.navigational_status, p.rot, p.sog, p.cog, p.heading, p.imo, p.callsign, p.name, p.ship_type, p.width, p.length, p.type_of_position_fixing_device, p.draught, p.destination, p.trip_id, p.simplified_trip_id, None])

#     df_all_points = pd.DataFrame(total_trip_points, columns=COLUMNS)
#     return df_all_points

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