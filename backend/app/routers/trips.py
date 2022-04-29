from random import randint
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_token_header, get_logger
from app.models.coordinate import Coordinate
from app.models.grid_polygon import GridPolygon
from app.models.simplified_line_string import SimplifiedLineString
from app.models.location import Location
from app.models.trip import Trip
from app.db.database import engine, Session
from app.db.queries.trip_queries import query_get_points_in_line_string, get_polygons, get_points, get_line_strings
from shapely.geometry import Point
from dotenv import load_dotenv
import shapely.wkb as wkb
import geopandas as gpd
import pandas as pd
import os
import json

load_dotenv()
API_LOG_FILE_PATH = os.getenv('API_LOG_FILE_PATH')

session = Session()
logger = get_logger(API_LOG_FILE_PATH)
router = APIRouter(
    prefix="/trips",
    tags=["trips"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.post('/')
async def get_trips(p1: Coordinate, p2: Coordinate): 
    gp1 = Point(p1.long, p1.lat)
    gp2 = Point(p2.long, p2.lat)

    # First we fetch the hexagons for where two points can be found inside
    logger.info('Fetching polygons...')

    # The check of the p1.is_hexagon and p1.grid_size should probably be in a function on its own
    # and then returned to here, to be given to the function call
    poly_df = get_polygons(gp1, gp2, p1.is_hexagon, p1.grid_size, logger)
    pd.options.display.max_colwidth = 10000
    
    # We add the hexagons to a list, so that we can access these values later
    polygons_list = add_polygons_to_list(poly_df)
    logger.info('Polygons fetched!')
    
    logger.info('Fetching line strings')
    line_string_df = get_line_strings(poly1=polygons_list[0], poly2=polygons_list[1], logger=logger)
    # with open('/srv/data/csv/line_strings.json', 'w') as out_file:
    #     out_file.write(line_string_df.to_json())

    # Do the ETA calculations
    line_string_df['c1_time'] = (pd.to_timedelta((line_string_df['dist_df_loc1_c1'] / line_string_df['df_loc1_sog']),unit='s') + line_string_df['df_loc1_time_id'])
    line_string_df['c2_time'] = (pd.to_timedelta((line_string_df['dist_df_loc2_c2'] / line_string_df['df_loc2_sog']),unit='s') + line_string_df['df_loc2_time_id'])
    
    line_string_df['eta'] = (line_string_df['c2_time'] - line_string_df['c1_time']).astype(str)
    print("-------------")
    line_string_df = line_string_df.drop(columns=['df_loc1', 'df_loc1_time_id', 'df_loc1_sog', 'dist_df_loc1_c1', 'df_loc2', 'df_loc2_time_id', 'df_loc2_sog', 'dist_df_loc2_c2', 'c1_time', 'c2_time'],axis=1, errors='ignore')
    logger.info('Line strings fetched!')
    
    line_string_df['color'] = line_string_df.apply(lambda x: give_color(), axis=1)

    print(line_string_df['line_string'].count())

    return line_string_df.to_json()
    
    if len(point_from_line_string_found_in_hexagon) == 0: # In case no points were found insecting, find centroids for points closest to both hexagons
        print('No points in either hexagons')
        for hex in hexagons:
            create_point(hex, query_get_points_in_line_string(), hexagons) 
    elif len(point_from_line_string_found_in_hexagon) == 1: # find centroid for points closest to the missing hexagon
        # Find which hexagon has no points
        for hex in hexagons:
            if hex not in point_from_line_string_found_in_hexagon:
                create_point(hex, query_get_points_in_line_string(), hexagons)
    # else:     
    #     hex1_df = group.get_group(hexagons_list[0])
    #     hex2_df = group.get_group(hexagons_list[1])

    #     countSeries = df['hexgeom'].value_counts()
    #     print('Prints in else')
    #     pointsInHex1 = countSeries[0]
    #     print(pointsInHex1)
    #     pointsInHex2 = countSeries[1]
    #     print(pointsInHex2)
    #     print(f"There are {pointsInHex1} points in the first hexagon, and {pointsInHex2} points in the second hexagon")
    #     if pointsInHex1 != pointsInHex2:
    #         if pointsInHex1 > pointsInHex2:
    #             diff = pointsInHex1 - pointsInHex2
    #             hex1_df = hex1_df.iloc[:-diff]
    #         else:
    #             diff = pointsInHex2 - pointsInHex1
    #             hex2_df = hex2_df.iloc[:-diff]
        

    return line_string_to_return_to_frontend

def create_point(hexagon: GridPolygon, linestring: str, hexagons: list[GridPolygon]):
    # point_query =   f'''{linestring}
    #                 WITH nearest_point AS (
    #                     SELECT 
    #                         ST_ClosestPoint(%(hex)s::geometry, pil.geom) AS geom
    #                     FROM
    #                         points_in_linestring AS pil
    #                     WHERE
    #                         ST_Intersects(
    #                             ST_FlipCoordinates(std.line_string),
    #                             %(hex1geom)s::geometry
    #                         ) AND
    #                         ST_Intersects(
    #                             ST_FlipCoordinates(std.line_string),
    #                             %(hex2geom)s::geometry
    #                         )     
    #                 )
    #                 '''
    point_query =   f'''{linestring}
                    SELECT 
                        DISTINCT ST_ClosestPoint(%(hex)s::geometry, pil.geom) AS geom
                    FROM
                        points_in_linestring AS pil;
                    '''
    # Get the closest point to the hexagon, so we can use the data from that point.            
    # Calculate the distance from ST_ClosestPoint(ST_Centroid(hexagon), linestring) to the point found before.
    # Then we can use SOG of the point in the linestring, and the distance to calculate a timestamp.
    # query = f'''{linestring}
    #             SELECT 
    #                 date_dim.date_id, data_fact.sog, pil.geom, ship_type_dim.ship_type, h.hex_10000_row, h.hex_10000_column
    #             FROM 
    #                 data_fact
    #                 INNER JOIN date_dim ON date_dim.date_id = data_fact.date_id 
    #                 INNER JOIN time_dim ON time_dim.time_id = data_fact.time_id
    #                 INNER JOIN ship_type_dim ON ship_type_dim.ship_type_id = data_fact.ship_type_id
    #                 INNER JOIN points_in_linestring AS pil ON pil.simplified_trip_id = data_fact.simplified_trip_id
    #             WHERE
    #                 ST_ClosestPoint(%(hex)s::geometry, )
    # '''
    df = pd.read_sql_query( 
            point_query, 
            engine,
            params={
                'hex1row': hexagons[0].row,
                'hex1column': hexagons[0].column,
                'hex1hex': wkb.dumps(hexagons[0].polygon, hex=True, srid=4326),
                'hex2row': hexagons[1].row,
                'hex2column': hexagons[1].column,
                'hex2hex': wkb.dumps(hexagons[1].polygon, hex=True, srid=4326),
                'hex': wkb.dumps(hexagon.polygon, hex=True, srid=4326) 
            }
        )
    return []





def get_list_of_line_strings_with_points(line_string_df: gpd.GeoDataFrame, 
                                  points_df: gpd.GeoDataFrame) -> dict[SimplifiedLineString]:

    simplified_line_strings_list = {}
    simplified_line_strings_list: list[SimplifiedLineString]

    line_string_df = line_string_df.fillna('')
    points_df = points_df.fillna('')
    
    for simplified_trip_id, line_string, mmsi, type_of_mobile, imo, name, width, length, ship_type in zip(line_string_df.simplified_trip_id, line_string_df.line_string, line_string_df.mmsi, line_string_df.type_of_mobile, line_string_df.imo, line_string_df.name, line_string_df.width, line_string_df.length, line_string_df.ship_type):
        line_class_object = SimplifiedLineString(simplified_trip_id=simplified_trip_id, 
                                                line_string=line_string, 
                                                locations=[],
                                                mmsi=mmsi,
                                                imo=imo,
                                                name=name,
                                                type_of_mobile=type_of_mobile,
                                                width=width,
                                                length=length,
                                                ship_type=ship_type)
        simplified_line_strings_list[simplified_trip_id] = line_class_object
    

    for row, col, location, simplified_trip_id, date_id, time_id, sog in zip(points_df.row, points_df.col, points_df.location, points_df.simplified_trip_id, points_df.date_id, points_df.time_id, points_df.sog):
        line_class_object = simplified_line_strings_list.get(simplified_trip_id)
        line_class_object: SimplifiedLineString
        line_class_object.locations.append(
            Location(
                row=row, 
                column=col, 
                location=location, 
                date_id=date_id, 
                time_id=time_id, 
                sog=sog)
            )

    return simplified_line_strings_list

def add_polygons_to_list(df: pd.DataFrame) -> list[GridPolygon]:
    polygons = []
    
    for table_row in df.itertuples(name=None):
        polygons.append(GridPolygon(column=table_row[2], row=table_row[1], polygon=table_row[3], centroid=table_row[4]))
    
    return polygons




        # create_point_query = f'''hexagon_centroid AS (
    #                                 SELECT
    #                                     DISTINCT date_dim.date_id, time_dim.time, data_fact.sog,
    #                                     ST_Centroid(hex1.geom) AS geom
    #                                 FROM
    #                                     points_in_linestring AS pil, hex1, hex2, data_fact, date_dim, time_dim
    #                                 WHERE
    #                                     pil.simplified_trip_id = data_fact.simplified_trip_id AND
    #                                     data_fact.date_id = date_dim.date_id AND
    #                                     data_fact.time_id = time_dim.time_id AND
    #                                     pil.geom = data_fact.location
    #                                 LIMIT 1
    #                          )'''


def give_color():
            return f'rgb({randint(0, 255)}, {randint(0, 255)}, {randint(0, 255)})'