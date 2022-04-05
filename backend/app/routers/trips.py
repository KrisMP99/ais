from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_token_header, get_logger
from app.models.coordinate import Coordinate
from app.db.database import engine, Session
from geojson import Point, Polygon
import asyncio
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
    gp1 = Point((p1.long, p1.lat))
    gp2 = Point((p2.long, p2.lat))

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

    polygons = []
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, pd.read_sql_query, polygon_query, engine)
    if len(result['st_asgeojson']) <= 1:
        logger.error('The two coordinates intersect with each other')
        return []
    polygons.append(Polygon([result['st_asgeojson'][0]['coordinates'][0]]))
    polygons.append(Polygon([result['st_asgeojson'][1]['coordinates'][0]]))

    
    hexagon_query = f"WITH hexagons AS (                                                     \
                            SELECT                                                              \
                                ST_AsText(                                                      \
                                    ST_GeomFromGeoJSON('{polygons[0]}')) As hex1,              \
                                ST_AsText(                                                      \
                                    ST_GeomFromGeoJSON('{polygons[1]}')) As hex2)"

    # Then we select all linestrings that intersect with the two polygons
    linestring_query = f"{hexagon_query}                                                        \
                        SELECT                                                                  \
                            ST_AsGeoJSON(std.line_string)::json AS st_asgeojson                 \
                        FROM                                                                    \
                            simplified_trip_dim as std, hexagons                                \
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
        print(chunk)
        if len(chunk) != 0:
            for json in chunk['st_asgeojson']:
                if json is not None:
                    linestrings.append(json['coordinates'])
        else:
            logger.warning('No trips were found for the selected coordinates')
            raise HTTPException(status_code=404, detail='No trips were found for the selected coordinates')
    

    linestring_points_query = f"{hexagon_query},                                                                              \
                    points_in_linestring AS (                                                       \
                        SELECT                                                                      \
                            ST_PointN(                                                              \
                                std.line_string,                                                    \
                                generate_series(1, ST_NPOINTS(std.line_string))                     \
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
    print("HERE M8")
    point_exists_in_hexagon_query = f"{linestring_points_query}                                                                    \
                                    SELECT                                                                      \
                                        DISTINCT date_dim.date_id, time_dim.time, data_fact.sog, pil.geom,      \
                                        ship_type_dim.ship_type                                                 \
                                    FROM                                                                        \
                                        points_in_linestring AS pil, data_fact, date_dim, time_dim, hexagons,   \
                                        ship_type_dim                                                           \
                                    WHERE                                                                       \
                                        pil.simplified_trip_id = data_fact.simplified_trip_id AND               \
                                        data_fact.date_id = date_dim.date_id AND                                \
                                        data_fact.time_id = time_dim.time_id AND                                \
                                        pil.geom = data_fact.location AND                                       \
                                        ST_Within(                                                              \
                                                    ST_FlipCoordinates(pil.geom),                               \
                                                    ST_SetSRID(hexagons.hex1, 3857)                             \
                                        ) OR                                                                    \
                                        ST_Within(                                                              \
                                                    ST_FlipCoordinates(pil.geom),                               \
                                                    ST_SetSRID(hexagons.hex2, 3857)                             \
                                        )                                                                       \
                                    ORDER BY time_dim.time                                                      \
                                    LIMIT 1;"

    create_point_query = f"hexagon_centroid AS (                                                           \
                                    SELECT                                                                      \
                                        DISTINCT date_dim.date_id, time_dim.time, data_fact.sog,                \
                                        ST_Centroid(hex1.geom) AS geom                                          \
                                    FROM                                                                        \
                                        points_in_linestring AS pil, hex1, hex2, data_fact, date_dim, time_dim  \
                                    WHERE                                                                       \
                                        pil.simplified_trip_id = data_fact.simplified_trip_id AND               \
                                        data_fact.date_id = date_dim.date_id AND                                \
                                        data_fact.time_id = time_dim.time_id AND                                \
                                        pil.geom = data_fact.location                                           \
                                    LIMIT 1                                                                     \
                                )"
    print('made it this far')
    for chunk in pd.read_sql_query(point_exists_in_hexagon_query, engine, chunksize=50000):
        if len(chunk) != 0:
            print(chunk)
        else:
            logger.warning('Could not find any hexagons')

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