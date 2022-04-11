from typing import List
from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_token_header, get_logger
from app.models.coordinate import Coordinate
from app.models.hexagon import Hexagon
from app.db.database import engine, Session
from shapely import wkb
from shapely.geometry import Point
import asyncio
import pandas as pd
import numpy as np

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
    geomp1 = Point(p1.long, p1.lat)
    geomp2 = Point(p2.long, p2.lat)
    print('start')
    # First we select the two polygon where the points choosen reside
    hexagon_query = '''                                                         
                        SELECT                                                          
                            h.hid, h.geom                                               
                        FROM                                                            
                            hexagrid as h                           
                        WHERE                                                           
                            ST_Intersects(
                                h.geom, ST_GeomFromWKB(%(p1)s::geometry, 3857)
                            ) OR     
                            ST_Intersects(
                                h.geom, ST_GeomFromWKB(%(p2)s::geometry, 3857)
                            );
                    '''

    print('tried gettings hexagons')
    hexagons = []

    df = pd.read_sql_query(hexagon_query, 
                          engine,
                          params={
                              "p1": geomp1.wkb_hex,
                              "p2": geomp2.wkb_hex
                          })
    if len(df) < 2:
        logger.error('The two coordinates intersect with each other')
        return []
    
    for row in df.itertuples():
        hexagons.append(Hexagon(hid=row.hid, geom=row.geom))

    print('Got hexagons. Began getting linestrings')

    # Then we select all linestrings that intersect with the two polygons
    linestring_query =  '''
                        SELECT
                            ST_AsGeoJSON(std.line_string)::json AS st_asgeojson
                        FROM
                            simplified_trip_dim AS std
                        WHERE
                            ST_Intersects(
                                ST_FlipCoordinates(std.line_string),
                                %(hex1geom)s::geometry
                            ) AND
                            ST_Intersects(
                                ST_FlipCoordinates(std.line_string),
                                %(hex2geom)s::geometry
                            );
                        '''

    # linestring_query = "SELECT ST_AsGeoJSON(td.line_string)::json AS st_asgeojson FROM simplified_trip_dim AS td"

    linestrings = []
    
    # Fills the linestring array, so we can return linestrings to frontend
    for chunk in pd.read_sql_query(
                        linestring_query, 
                        engine, 
                        params=
                        {
                            "hex1geom": hexagons[0].geom, 
                            "hex2geom": hexagons[1].geom
                        }, 
                        chunksize=50000):
        if len(chunk) != 0:
            for json in chunk['st_asgeojson']:
                if json is not None:
                    linestrings.append(json['coordinates'])
        else:
            logger.warning('No trips were found for the selected coordinates')
            raise HTTPException(status_code=404, detail='No trips were found for the selected coordinates')
    print('Got linestrings')

    # Select all points in the linestrings insecting the hexagons
    linestring_points_query =   '''
                                WITH points_in_linestring AS (
                                    SELECT DISTINCT
                                        ST_PointN(
                                            std.line_string,
                                            generate_series(1, ST_NPoints(std.line_string))
                                        ) AS geom, std.simplified_trip_id
                                    FROM
                                        simplified_trip_dim AS std
                                    WHERE
                                        ST_Intersects(
                                            ST_FlipCoordinates(std.line_string),
                                            %(hex1geom)s::geometry
                                        ) AND
                                        ST_Intersects(
                                            ST_FlipCoordinates(std.line_string),
                                            %(hex2geom)s::geometry
                                        )
                                )
                                '''
    # Select points that intersect with either of the hexagons
    point_exists_in_hexagon_query = f'''{linestring_points_query}
                                    SELECT
                                        date_dim.date_id, time_dim.time_id,
                                        data_fact.sog, pil.geom, ship_type_dim.ship_type,
                                        h.hid

                                    FROM
                                        hexagrid AS h, data_fact
                                        INNER JOIN date_dim ON date_dim.date_id = data_fact.date_id 
                                        INNER JOIN time_dim ON time_dim.time_id = data_fact.time_id
                                        INNER JOIN ship_type_dim ON ship_type_dim.ship_type_id = data_fact.ship_type_id
                                        INNER JOIN points_in_linestring AS pil ON pil.simplified_trip_id = data_fact.simplified_trip_id
                                    WHERE
                                        data_fact.location = pil.geom AND
                                        (
                                            (ST_Within(
                                                    ST_FlipCoordinates(pil.geom),
                                                    %(hex1geom)s::geometry
                                            ) AND 
                                            h.hid = %(hex1hid)s) OR
                                            
                                            (ST_Within(
                                                    ST_FlipCoordinates(pil.geom),
                                                    %(hex2geom)s::geometry
                                            ) AND 
                                            h.hid = %(hex2hid)s)
                                        )
                                    ORDER BY time_dim.time_id
                                    '''

    # create_point_query = f"hexagon_centroid AS (                                                           \
    #                                 SELECT                                                                      \
    #                                     DISTINCT date_dim.date_id, time_dim.time, data_fact.sog,                \
    #                                     ST_Centroid(hex1.geom) AS geom                                          \
    #                                 FROM                                                                        \
    #                                     points_in_linestring AS pil, hex1, hex2, data_fact, date_dim, time_dim  \
    #                                 WHERE                                                                       \
    #                                     pil.simplified_trip_id = data_fact.simplified_trip_id AND               \
    #                                     data_fact.date_id = date_dim.date_id AND                                \
    #                                     data_fact.time_id = time_dim.time_id AND                                \
    #                                     pil.geom = data_fact.location                                           \
    #                                 LIMIT 1                                                                     \
    #                             )"

    df = pd.read_sql_query( 
            point_exists_in_hexagon_query, 
            engine,
            params={
                'hex1hid': hexagons[0].hid,
                'hex1geom': hexagons[0].geom,
                'hex2hid': hexagons[1].hid,
                'hex2geom': hexagons[1].geom
            }
        )
    hexagons_list = df['hid'].unique().tolist()
    group = df.groupby(by=['hid'])
    
    print('Number of groups ', group.ngroups)

    if group.ngroups == 0: # In case no points were found insecting, find centroids for points closest to both hexagons
        print('No points in either hexagons')
        for hex in hexagons:
            create_point(hex, linestring_points_query, hexagons) 
    elif group.ngroups == 1: # find centroid for points closest to the missing hexagon
        # Find which hexagon has no points
        for hex in hexagons:
            if hex.hid not in hexagons_list:
                create_point(hex, linestring_points_query, hexagons)
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
        

    return linestrings

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
                        DISTINCT pil.geom
                    FROM
                        points_in_linestring AS pil;
                    WHERE ST_ClosestPoint(%(hex)s::geometry, pil.geom)
                '''
    # Get the closest point to the hexagon, so we can use the data from that point.            
    # Calculate the distance from ST_ClosestPoint(ST_Centroid(hexagon), linestring) to the point found before.
    # Then we can use SOG of the point in the linestring, and the distance to calculate a timestamp.
    # query = f'''{linestring}
    #             SELECT 
    #                 date_dim.date_id, data_fact.sog, pil.geom, ship_type_dim.ship_type, h.hid
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
                'hex1hid': hexagons[0].hid,
                'hex1geom': hexagons[0].geom,
                'hex2hid': hexagons[1].hid,
                'hex2geom': hexagons[1].geom,
                'hex': hexagon.geom 
            }
        )
    print(df)
    return []