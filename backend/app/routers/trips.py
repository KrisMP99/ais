from lib2to3.pgen2.pgen import DFAState
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_token_header, get_logger
from app.models.coordinate import Coordinate
from app.models.hexagon import Hexagon
from app.models.simplified_line_string import SimplifiedLineString
from app.models.location import Location
from app.db.database import engine, Session
from app.db.queries.trip_queries import query_fetch_hexagons_given_two_points, query_fetch_line_strings_given_hexagons, query_get_points_in_line_string, query_point_exists_in_hexagon
from shapely.geometry import Point
from shapely.ops import transform
import shapely.wkb as wkb
import geopandas as gpd
import pandas as pd

session = Session()
logger = get_logger()
router = APIRouter(
    prefix="/trips",
    tags=["trips"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.post('/')
async def get_trip(p1: Coordinate, p2: Coordinate): 
    gp1 = Point(p1.long, p1.lat)
    gp2 = Point(p2.long, p2.lat)

    # First we fetch the hexagons for where two points can be found inside
    logger.info('Fetching hexagon!')
    query_hexagons = query_fetch_hexagons_given_two_points()
    hex_df = get_hexagons(query_hexagons, gp1, gp2)

    if len(hex_df) < 2:
        logger.error('The two coordinates intersect with each other')
        return []
    
    # We add the hexagons to a list, so that we can access these values later
    hexagons = add_hexagons_to_list(hex_df)

    logger.info('Hexagons fetched!')
    
    # linestring_query = "SELECT ST_AsGeoJSON(td.line_string)::json AS st_asgeojson FROM simplified_trip_dim AS td"

    logger.info('Fetching line strings')
    query_line_strings_for_hexagons = query_fetch_line_strings_given_hexagons()
    query_points_in_line_string = query_get_points_in_line_string()

    line_string_df = get_line_strings(query_line_strings_for_hexagons, hex1=hexagons[0], hex2=hexagons[1])
    
    if len(line_string_df) == 0:
        logger.warning('No trips were found for the selected coordinates')
        raise HTTPException(status_code=404, detail='No trips were found for the selected coordinates')

    points_in_line_string_df = get_points(query_points_in_line_string, hex1=hexagons[0], hex2=hexagons[1])
    
    line_strings = get_list_of_line_strings_with_points(line_string_df=line_string_df, 
                                                 points_df=points_in_line_string_df)

    logger.info('Line strings fetched!')

    # Create array with points from line strings and check if either hexagon appears in any of the points
    line_string_to_return_to_frontend = []
    for l_key in line_strings.copy():
        line_string = line_strings[l_key]
        line_string:SimplifiedLineString

        locations = []
        point_from_line_string_found_in_hexagon = [Hexagon]
        for coordinate in line_string.locations:
            coordinate:Location

            print('simplified_trip_id ', line_string.simplified_trip_id)
            # Add points to frontend
            locations.append([coordinate.location.y, coordinate.location.x])

            # Checks if the points is in the hexagon

            print('coordinate ', coordinate.hex_10000_column)
            print('hex ', hexagons[0].column)

            isSame = coordinate.hex_10000_column is hexagons[0].column
            print('is same ', isSame)

            if coordinate.hex_10000_column is hexagons[0].column and coordinate.hex_10000_row is hexagons[0].row:
                point_from_line_string_found_in_hexagon.append(hexagons[0])

                print('hex column ' + str(coordinate.hex_10000_column) + ' , hex row ' + str(coordinate.hex_10000_row))
                print('hex column ' + str(hexagons[0].column) + ' , hex row ' + str(hexagons[0].row))

            elif coordinate.hex_10000_column is hexagons[1].column and coordinate.hex_10000_row is hexagons[1].row:
                point_from_line_string_found_in_hexagon.append(hexagons[1])
                print('hex column ' + coordinate.hex_10000_column + ' , hex row ' + coordinate.hex_10000_row)
                print('hex column ' + hexagons[1].column + ' , hex row ' + hexagons[1].row)
            else: 
                print('continued')
                continue


        line_string_to_return_to_frontend.append(locations)
    print('length of list ' + str(len(point_from_line_string_found_in_hexagon)))
    print('what is in the list ', str(point_from_line_string_found_in_hexagon))
    logger.info('Got linestrings')
    
    return line_string_to_return_to_frontend
    
    df = gpd.read_postgis( 
            query_point_exists_in_hexagon(), 
            engine,
            params={
                'hex1row': hexagons[0].row,
                'hex1column': hexagons[0].column,
                'hex1hex': hexagons[0].hexagon.wkb_hex,
                'hex2row': hexagons[1].row,
                'hex2column': hexagons[1].column,
                'hex2hex': hexagons[1].hexagon.wkb_hex,
            },
            geom_col='geom'
        )

    print(df)

    hexagons_list = pd.unique(df[['hex_10000_row', 'hex_10000_column']].values.ravel('K')).tolist()

    group = df.groupby(by=['hex_10000_row', 'hex_10000_column'])
    
    print('Number of groups ', group.ngroups)

    if group.ngroups == 0: # In case no points were found insecting, find centroids for points closest to both hexagons
        print('No points in either hexagons')
        for hex in hexagons:
            create_point(hex, query_get_points_in_line_string(), hexagons) 
    elif group.ngroups == 1: # find centroid for points closest to the missing hexagon
        # Find which hexagon has no points
        for hex in hexagons:
            if hex.row not in hexagons_list and hex.column not in hexagons_list:
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

def create_point(hexagon: Hexagon, linestring: str, hexagons: list[Hexagon]):
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
                'hex1hex': wkb.dumps(hexagons[0].hexagon, hex=True, srid=4326),
                'hex2row': hexagons[1].row,
                'hex2column': hexagons[1].column,
                'hex2hex': wkb.dumps(hexagons[1].hexagon, hex=True, srid=4326),
                'hex': wkb.dumps(hexagon.hexagon, hex=True, srid=4326) 
            }
        )
    return []

def get_line_strings(query: str, hex1: Hexagon, hex2: Hexagon) -> pd.DataFrame:
    df = gpd.read_postgis(
            query, 
            engine, 
            params=
            {
                "hex1": wkb.dumps(hex1.hexagon, hex=True, srid=4326), 
                "hex2": wkb.dumps(hex2.hexagon, hex=True, srid=4326)
            },
            geom_col='line_string'
        )
    return df

def get_points(query: str, hex1: Hexagon, hex2: Hexagon) -> pd.DataFrame:
    df = gpd.read_postgis(
        query, 
        engine, 
        params=
        {
            "hex1": wkb.dumps(hex1.hexagon, hex=True, srid=4326), 
            "hex2": wkb.dumps(hex2.hexagon, hex=True, srid=4326)
        },
        geom_col='location')
    return df

def get_list_of_line_strings_with_points(line_string_df: gpd.GeoDataFrame, 
                                  points_df: gpd.GeoDataFrame) -> dict[SimplifiedLineString]:

    simplified_line_strings_list = {}
    simplified_line_strings_list: list[SimplifiedLineString]
    
    for simplified_trip_id, line_string in zip(line_string_df.simplified_trip_id, line_string_df.line_string):
        line = SimplifiedLineString(simplified_trip_id=simplified_trip_id, line_string=line_string, locations=[])
        simplified_line_strings_list[simplified_trip_id] = line

    for hex_10000_row, hex_10000_column, location, simplified_trip_id, date_id, time_id, ship_type, sog in zip(points_df.hex_10000_row, points_df.hex_10000_column, points_df.location, points_df.simplified_trip_id, points_df.date_id, points_df.time_id, points_df.ship_type, points_df.sog):
        line_class = simplified_line_strings_list.get(simplified_trip_id)
        line_class: SimplifiedLineString
        line_class.locations.append(
            Location(
                hex_10000_row=hex_10000_row, 
                hex_10000_column=hex_10000_column, 
                location=location, 
                date_id=date_id, 
                time_id=time_id, 
                ship_type=ship_type, 
                sog=sog)
            )

    return simplified_line_strings_list

def add_hexagons_to_list(df: pd.DataFrame) -> list[Hexagon]:
    hexagons = []
    
    for table_row in df.itertuples():
        hexagons.append(Hexagon(column=table_row.hex_10000_column, row=table_row.hex_10000_row, hexagon=table_row.hexagon))
    
    return hexagons

def get_hexagons(query: str, p1: Point, p2: Point) -> pd.DataFrame:
    '''Returns the hexagons where p1 and p2 can be found within'''
    df = gpd.read_postgis(
            query, 
            engine,
            params={
                "p1": wkb.dumps(p1, hex=True, srid=4326),
                "p2": wkb.dumps(p2, hex=True, srid=4326)
            },
            geom_col='hexagon'
        )
    return df


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