from venv import create
import pandas as pd
import geopandas as gpd
from shapely.geometry import LineString, Point
from trips_partitioning import get_data_from_query

COLUMNS = ['timestamp', 'type_of_mobile', 'mmsi','latitude','longitude', 'navigational_status', 'rot', 'sog', 'cog', 'heading', 'imo', 'callsign', 'name', 'ship_type', 'width', 'length', 'type_of_position_fixing_device', 'draught', 'destination', 'trip_id', 'simplified_trip_id']

# Tolerance for Douglas Peucker algorithm
TOLERANCE = 1000

# def create_trip_line_strings(df: gpd.GeoDataFrame, logger) -> gpd.GeoDataFrame:
#     logger.info("Creating line strings for trip_dim...")
#     trip_df = df.groupby(by=['trip_id'])['geometry'].apply(lambda x: LineString(x.tolist()))
#     trip_df = gpd.GeoDataFrame({'trip_id':trip_df.index, 'line_string':trip_df.values}, geometry='line_string', crs="EPSG:3857").set_index('trip_id')
#     return trip_df

def create_simplified_trip_line_strings(df: gpd.GeoDataFrame, logger) -> gpd.GeoDataFrame:
    sql = "SELECT MAX(simplified_trip_dim.simplified_trip_id) FROM simplified_trip_dim"
    keys_df = get_data_from_query(sql)
    simplified_trip_PK_key = keys_df['max'].values[0]

    if simplified_trip_PK_key is None:
        simplified_trip_PK_key = 1
    else:
        simplified_trip_PK_key += 1

    logger.info("Creating line strings for simplified trip dim")
    df = df.sort_values(by=['timestamp'])

    simplified_trip_df = df.groupby(by=['trip_id'], as_index=False)['geometry'].apply(lambda x: LineString(x.tolist()).simplify(tolerance=TOLERANCE,preserve_topology=False))
    simplified_trip_df = gpd.GeoDataFrame(simplified_trip_df, geometry='geometry', crs="EPSG:3857")
    simplified_trip_df.insert(0,'simplified_trip_id',range(simplified_trip_PK_key, simplified_trip_PK_key + len(simplified_trip_df)))
    simplified_trip_df = simplified_trip_df.rename_geometry('line_string')

    return simplified_trip_df


def add_id(row, simplified_trip_df: gpd.GeoDataFrame):
    trip_id = row['trip_id'].iloc[0]
    result: gpd.GeoSeries
    result = simplified_trip_df[(simplified_trip_df['simplified_trip_id'] == trip_id)]
    coords = result['line_string'].iloc[0].xy

    row['simplified_trip_id'] = None
    for x, y in zip(coords[0], coords[1]):
        for point in row.itertuples(name=None):
            point_x_y = point[21].xy
            if x == point_x_y[0][0] and y == point_x_y[1][0]:
                row['simplified_trip_id'] = trip_id
                break

    return row
    
# TODO: Change prints to logging    
def add_simplified_trip_ids(df: gpd.GeoDataFrame, simplified_trip_df: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    df = df.groupby(by='trip_id', as_index=False).apply(lambda x: add_id(x, simplified_trip_df))
    # df = gpd.GeoDataFrame(df, geometry='geometry', crs="EPSG:3857")

    # df = df.drop(columns=['point'])
    # data: gpd.GeoDataFrame
    # data = gpd.sjoin(df, simplified_trip_df, how='left', predicate='touches')
    # print(data)
    # df['simplified_trip_id'] = data['index_right'] + 1

    # print("Len of df:", len(df))
    # print(data['index_right'].value_counts())
    # print("Finished adding simplified trip ids")
    return df

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