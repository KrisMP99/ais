from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_token_header, get_logger
from app.models.coordinate import Coordinate
from app.models.hexagon import Hexagon
from app.db.database import engine, Session
from geojson import Point
from shapely import wkb
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
    gp1 = Point((p1.long, p1.lat))
    gp2 = Point((p2.long, p2.lat))
    print('start')
    # First we select the two polygon where the points choosen reside
    hexagon_query = f"WITH point1 AS (                                              \
                        SELECT                                                      \
                            ST_AsText(ST_GeomFromGeoJSON('{gp1}')) As geom),        \
                                                                                    \
                    point2 AS (                                                     \
                        SELECT                                                      \
                            ST_AsText(ST_GeomFromGeoJSON('{gp2}')) As geom)         \
                                                                                    \
                    SELECT                                                          \
                        h.hid, h.geom                                               \
                    FROM                                                            \
                        hexagrid as h, point1, point2                               \
                    WHERE                                                           \
                        ST_Intersects(h.geom, ST_SetSRID(point1.geom, 3857)) OR     \
                        ST_Intersects(h.geom, ST_SetSRID(point2.geom, 3857));"

    print('tried gettings hexagons')
    hexagons = []
    loop = asyncio.get_event_loop()
    df = await loop.run_in_executor(None, pd.read_sql_query, hexagon_query, engine)
    if len(df) < 2:
        logger.error('The two coordinates intersect with each other')
        return []
    
    for row in df.itertuples():
        hexagons.append(Hexagon(hid=row.hid, geom=row.geom))

    print('Got hexagons. Began getting linestrings')

    # Then we select all linestrings that intersect with the two polygons
    linestring_query =  """
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
                        """

    # linestring_query = "SELECT ST_AsGeoJSON(td.line_string)::json AS st_asgeojson FROM simplified_trip_dim AS td"

    linestrings = []
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
    print('got linestrings')

    linestring_points_query =   """
                                SELECT
                                    ST_PointN(
                                        std.line_string,
                                        generate_series(1, ST_NPoints(std.line_string))
                                    ) AS geom, std.simplified_trip_id, h.hid
                                FROM
                                    simplified_trip_dim AS std, hexagrid AS h
                                WHERE
                                    (h.hid = %(hex1hid)s OR
                                    h.hid = %(hex2hid)s) AND
                                    ST_Intersects(
                                        std.line_string,
                                        h.geom
                                    );
                                """

    # point_exists_in_hexagon_query = f"""{linestring_points_query}
    #                                 SELECT
    #                                     date_dim.date_id, time_dim.time_id,
    #                                     data_fact.sog, pil.geom, ship_type_dim.ship_type, pil.hid

    #                                 FROM
    #                                     points_in_linestring AS pil, data_fact, date_dim, time_dim, ship_type_dim
    #                                 WHERE
    #                                     data_fact.simplified_trip_id = pil.simplified_trip_id AND
    #                                     data_fact.date_id = date_dim.date_id AND
    #                                     data_fact.time_id = time_dim.time_id AND
    #                                     data_fact.location = pil.geom AND
    #                                     data_fact.ship_type_id = ship_type_dim.ship_type_id AND
    #                                     (ST_Within(
    #                                                 ST_FlipCoordinates(pil.geom),
    #                                                 %(hex1geom)s::geometry
    #                                     ) OR
    #                                     ST_Within(
    #                                                 ST_FlipCoordinates(pil.geom),
    #                                                 %(hex2geom)s::geometry
    #                                     ))
    #                                 ORDER BY time_dim.time_id
    #                                 """

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
        linestring_points_query, 
        engine,
        params={
            'hex1hid': hexagons[0].hid,
            'hex1geom': hexagons[0].geom,
            'hex2hid': hexagons[1].hid,
            'hex2geom': hexagons[1].geom
        }
        )
    print(df)
    # hexagons_list = df['hid'].unique().tolist()
    # group = df.groupby(by=['hid'])
    
    # if group.ngroups == 0: # find centroids for points closest to both hexagons
    #     print('heeej')
    # elif group.ngroups == 1: # find centroid for points closest to the missing hexagon
    #     hex1_df = group.get_group(hexagons_list[0])
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
        



    # if len(result) == 0:
    #     print('No points')
    # elif len(result) == 1:
    #     print('1 point')
    # elif len(result) == 2 and result[0]['hexgeom'] != result[1]['hexgeom']:
    #     print('2 points and not in the same hexagon')
    #     print(result)
    # elif len(result) == 2 and result[0]['hexgeom'] == result[1]['hexgeom']:
    #     print('2 points and both points in the same hexagon')
    #     print(result)
    # elif len(result) > 2:
    #     print('More than 2 points')
    #     known_hex = result[0]['hexgeom']
    #     hex1 = { 'amount': 0, 'index': [] }
    #     hex2 = { 'amount': 0, 'index': [] }
    #     for hex in result:
    #         if hex['hexgeom'] == known_hex:
    #             hex1['amount'] += 1
    #             hex1['index'].append(result.index(hex))
    #         else: 
    #             hex2 += 1
    #             hex2['index'].append(result.index(hex))
    #     if hex1['amount'] != hex2['amount']:
    #         print('More than 2 points and not equally many in each hexagon')
    #         dif = hex1['amount'] - hex2['amount']
    #         if dif < 0:
    #             for i in reversed(hex2['index']):
    #                 if(len(hex2['index']) == len(hex1['index'])):
    #                     break
    #                 hex2['index'].pop()
    #                 result.pop(hex2['index'].index(i))
    # else:
    #     print('shit went wrong with length of ' + len(result))
    
    return linestrings
    # linestring_query_hexagon = f"SELECT                                                                          \
    #                                 DISTINCT date_dim.date_id, time_dim.time, data_fact.sog,                    \
    #                                     CASE                                                                    \
    #                                         WHEN EXISTS(SELECT point_in_hexagon.geom FROM point_in_hexagon)     \
    #                                             THEN point_in_hexagon.geom                                      \
    #                                         ELSE (SELECT hexagon_centroid.geom FROM hexagon_centroid)           \
    #                                     END AS geom                                                             \
    #                                 FROM                                                                        \
    #                                     points_in_linestring AS pil, hex1, hex2, data_fact, date_dim, time_dim, \
    #                                     point_in_hexagon, hexagon_centroid                                      \
    #                                 WHERE                                                                       \
    #                                     pil.simplified_trip_id = data_fact.simplified_trip_id AND               \
    #                                     data_fact.date_id = date_dim.date_id AND                                \
    #                                     data_fact.time_id = time_dim.time_id AND                                \
    #                                     pil.geom = data_fact.location;"