from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_token_header, get_logger
from app.models.coordinate import Coordinate
from app.db.database import engine, Session
from geojson import Point, Polygon
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
    polygon_query = f"WITH point1 AS (                                              \
                        SELECT                                                      \
                            ST_AsText(ST_GeomFromGeoJSON('{gp1}')) As geom),        \
                                                                                    \
                    point2 AS (                                                     \
                        SELECT                                                      \
                            ST_AsText(ST_GeomFromGeoJSON('{gp2}')) As geom)         \
                                                                                    \
                    SELECT                                                          \
                        ST_AsGeoJSON(h.geom)::json AS st_asgeojson                  \
                    FROM                                                            \
                        hexagrid as h, point1, point2                               \
                    WHERE                                                           \
                        ST_Intersects(h.geom, ST_SetSRID(point1.geom, 3857)) OR     \
                        ST_Intersects(h.geom, ST_SetSRID(point2.geom, 3857));"

    print('tried gettings hexagons')
    polygons = []
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, pd.read_sql_query, polygon_query, engine)
    if len(result['st_asgeojson']) <= 1:
        logger.error('The two coordinates intersect with each other')
        return []
    polygons.append(Polygon([result['st_asgeojson'][0]['coordinates'][0]]))
    polygons.append(Polygon([result['st_asgeojson'][1]['coordinates'][0]]))

    print('got hexagons. Began getting linestrings')
    hexagon_query = f"hexagons AS (                                                             \
                            SELECT                                                              \
                                ST_AsText(                                                      \
                                    ST_GeomFromGeoJSON('{polygons[0]}')) AS hex1,               \
                                ST_AsText(                                                      \
                                    ST_GeomFromGeoJSON('{polygons[1]}')) AS hex2) "

    # Then we select all linestrings that intersect with the two polygons
    linestring_query = f"WITH {hexagon_query}                                                   \
                        SELECT                                                                  \
                            ST_AsGeoJSON(std.line_string)::json AS st_asgeojson                 \
                        FROM                                                                    \
                            simplified_trip_dim AS std, hexagons                                \
                        WHERE                                                                   \
                            ST_Intersects(                                                      \
                                ST_FlipCoordinates(std.line_string),                            \
                                ST_SetSRID(hexagons.hex1, 3857)                                 \
                            ) AND                                                               \
                            ST_Intersects(                                                      \
                                ST_FlipCoordinates(std.line_string),                            \
                                ST_SetSRID(hexagons.hex2, 3857)                                 \
                            );"

    # linestring_query = "SELECT ST_AsGeoJSON(td.line_string)::json AS st_asgeojson FROM simplified_trip_dim AS td"

    linestrings = []
    for chunk in pd.read_sql_query(linestring_query, engine, chunksize=50000):
        if len(chunk) != 0:
            for json in chunk['st_asgeojson']:
                if json is not None:
                    linestrings.append(json['coordinates'])
        else:
            logger.warning('No trips were found for the selected coordinates')
            raise HTTPException(status_code=404, detail='No trips were found for the selected coordinates')
    print('got linestrings')

    linestring_points_query = f"WITH {hexagon_query},                                                                              \
                    points_in_linestring AS (                                                       \
                        SELECT                                                                      \
                            ST_PointN(                                                              \
                                std.line_string,                                                    \
                                generate_series(1, ST_NPoints(std.line_string))                     \
                            ) AS geom, std.simplified_trip_id                                       \
                        FROM                                                                        \
                            simplified_trip_dim AS std, hexagons                                    \
                        WHERE                                                                       \
                            ST_Intersects(                                                          \
                                ST_FlipCoordinates(std.line_string),                                \
                                ST_SetSRID(hexagons.hex1, 3857)                                     \
                            ) AND                                                                   \
                            ST_Intersects(                                                          \
                                ST_FlipCoordinates(std.line_string),                                \
                                ST_SetSRID(hexagons.hex2, 3857)                                     \
                            )                                                                       \
                    )"

    point_exists_in_hexagon_query = f"{linestring_points_query}                                                 \
                                    SELECT                                                                      \
                                        DISTINCT date_dim.date_id, time_dim.time_id, data_fact.sog, pil.geom,      \
                                        ship_type_dim.ship_type,                                                \
                                        CASE                                                                    \
                                            WHEN                                                                \
                                                ST_Within(                                                      \
                                                    ST_FlipCoordinates(pil.geom),                               \
                                                    ST_SetSRID(hexagons.hex1, 3857))                            \
                                                THEN (                                                          \
                                                    SELECT                                                      \
                                                        hexagons.hex1                                           \
                                                    FROM hexagons                                               \
                                                )                                                               \
                                            ELSE (                                                              \
                                                SELECT                                                          \
                                                    hexagons.hex2                                               \
                                                FROM hexagons                                                   \
                                            )                                                                   \
                                        END AS hexgeom                                                          \
                                    FROM                                                                        \
                                        points_in_linestring AS pil, data_fact, date_dim, time_dim, hexagons,   \
                                        ship_type_dim                                                           \
                                    WHERE                                                                       \
                                        data_fact.simplified_trip_id = pil.simplified_trip_id AND               \
                                        data_fact.date_id = date_dim.date_id AND                                \
                                        data_fact.time_id = time_dim.time_id AND                                \
                                        data_fact.location = pil.geom AND                                       \
                                        data_fact.ship_type_id = ship_type_dim.ship_type_id AND                 \
                                        (ST_Within(                                                             \
                                                    ST_FlipCoordinates(pil.geom),                               \
                                                    ST_SetSRID(hexagons.hex1, 3857)                             \
                                        ) OR                                                                    \
                                        ST_Within(                                                              \
                                                    ST_FlipCoordinates(pil.geom),                               \
                                                    ST_SetSRID(hexagons.hex2, 3857)                             \
                                        ))                                                                                                                            \
                                    ORDER BY time_dim.time"

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

    loop = asyncio.get_event_loop()
    df = await loop.run_in_executor(None, pd.read_sql_query, point_exists_in_hexagon_query, engine)
    hexagon1 = df['hexgeom'].values[0]
    hexagon2 = df['hexgeom'].values[1]

    hex1_df = df[(df['hexgeom'] == hexagon1)].reset_index()
    hex2_df = df[(df['hexgeom'] == hexagon2)].reset_index()

    countSeries = df['hexgeom'].value_counts()

    pointsInHex1 = countSeries[0]
    pointsInHex2 = countSeries[1]
    print(f"There are {pointsInHex1} points in the first hexagon, and {pointsInHex2} points in the second hexagon")

    if pointsInHex1 != pointsInHex2:
        if pointsInHex1 > pointsInHex2:
            hex1_df['diff'] = hex1_df['time_id'] - hex2_df['time_id']
        else:
            hex2_df['diff'] = hex2_df['time_id'] - hex1_df['time_id']
            
    print("Hex_df1: ", hex1_df.head())
    print("Hex_df2: ", hex2_df.head())



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