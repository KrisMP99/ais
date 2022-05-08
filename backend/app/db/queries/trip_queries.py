from logging import Logger
from re import S
from app.models.filter import Filter
from fastapi import HTTPException
from shapely.geometry import Point
from app.models.grid_polygon import GridPolygon
import pandas as pd
import geopandas as gpd
import shapely.wkb as wkb
from app.db.database import engine
import numpy as np

def query_fetch_polygons_given_two_points(p1_is_hex: bool, p1_size: int) -> str:
    '''We find all hexagons where the points are found in'''

    grid_sizes_hex = [500, 1000, 2500, 5000, 10000]
    grid_sizes_square = [806, 1612, 4030, 8060, 16120]
    
    if p1_is_hex:
        grid_type = "hex"
        if p1_size in grid_sizes_hex:
            size = p1_size
        else:
            raise HTTPException(status_code=404, detail=f'Grid size is not available for polygon type: {grid_type}, size: {p1_size}')
    else:
        grid_type = "square"
        if p1_size in grid_sizes_square:
            size = p1_size
        else:
            raise HTTPException(status_code=404, detail=f'Grid size is not available for polygon type: {grid_type}, size: {p1_size}')

    return f'''                                                         
                SELECT                                                          
                    h.{grid_type}_{size}_column, h.{grid_type}_{size}_row, h.grid_geom AS geom, h.centroid as centroid                                         
                FROM                                                            
                    {grid_type}_{size}_dim as h                           
                WHERE                                                           
                    ST_Within(
                        %(p1)s::geometry, h.grid_geom
                    ) OR     
                    ST_Within(
                        %(p2)s::geometry, h.grid_geom
                    );
            '''

def get_polygons(p1: Point, p2: Point, p1_is_hex: bool, p1_size: int, logger: Logger) -> pd.DataFrame:
    '''Returns the polygons where p1 and p2 can be found within'''
    sql_query = query_fetch_polygons_given_two_points(p1_is_hex, p1_size)

    df = gpd.read_postgis(
            sql_query, 
            engine,
            params={
                "p1": wkb.dumps(p1, hex=True, srid=4326),
                "p2": wkb.dumps(p2, hex=True, srid=4326)
            },
            geom_col='geom'
        )

    if len(df) < 2:
        logger.error('The two coordinates intersect with each other')
        return []

    return df

def query_line_strings_and_data_for_ETA(filter: Filter) -> str:
    filter_ship_type = ''
    if(filter.ship_types is not None and len(filter.ship_types) > 0):
        filter_ship_type += ' AND ('
        for ship_type in filter.ship_types[:-1]:
            filter_ship_type += f"ship_type_dim.ship_type = '{ship_type}' OR "
        filter_ship_type += f"ship_type_dim.ship_type = '{filter.ship_types[-1]}')"
    filter_nav_stats = ''
    if(filter.nav_stats is not None and len(filter.nav_stats) > 0):
        filter_nav_stats += ' AND ('
        for nav_status in filter.nav_stats[:-1]:
            filter_nav_stats += f"nav_dim.navigational_status = '{nav_status}' OR "
        filter_nav_stats += f"nav_dim.navigational_status = '{filter.nav_stats[-1]}')"

    return f'''WITH centroids_linestrings AS (
                SELECT
                    DISTINCT ON (std.simplified_trip_id) 
                    std.line_string as line_string, std.simplified_trip_id as simplified_id, 
                    ST_ClosestPoint(line_string, ST_GeomFromEWKT(%(centroid1)s)) as p1, 									
                    ST_ClosestPoint(line_string, ST_GeomFromEWKT(%(centroid2)s)) as p2	
                FROM
                    simplified_trip_dim AS std
                WHERE
                    ST_Intersects(std.line_string, ST_GeomFromEWKT(%(poly1)s))
                    AND
                    ST_Intersects(std.line_string, ST_GeomFromEWKT(%(poly2)s))
            ),
            segments AS (
                SELECT dumps.simplified_id, dumps.p1, dumps.p2, dumps.line_string as line_string,
                        ST_ReducePrecision(ST_MakeLine(
                                    lag((pt).geom, 1, NULL) 
                                    OVER (
                                            PARTITION BY dumps.simplified_id 
                                            ORDER BY dumps.simplified_id, (pt).path), (pt).geom
                                        ),0.0001) AS geom
                FROM (
                    SELECT centroids_linestrings.simplified_id, centroids_linestrings.p1, 
                        centroids_linestrings.p2, centroids_linestrings.line_string,
                        ST_DumpPoints(centroids_linestrings.line_string) AS pt 
                    FROM centroids_linestrings 
                ) as dumps

            ),
            result_seg_1 AS (
                SELECT DISTINCT ON (simplified_id) simplified_id as id1, segments.geom as seg1, segments.p1 as p1, segments.line_string
                FROM segments
                WHERE ST_DWithin(ST_Transform(segments.p1, 3857), ST_Transform(segments.geom, 3857), 1000)
            ),
            result_seg_2 AS (
                SELECT DISTINCT ON (simplified_id) simplified_id as id2, segments.geom as seg2, segments.p2 as p2
                FROM segments
                WHERE ST_DWithin(ST_transform(segments.p2, 3857), ST_Transform(segments.geom, 3857), 1000)
            ),
            get_data_1 AS (
                SELECT DISTINCT ON (data_fact.simplified_trip_id) 
                        result_seg_1.id1 as simplified_trip_id,
                        result_seg_1.line_string,
                        ship_dim.mmsi,
                        ship_dim.type_of_mobile,
                        ship_dim.imo,
                        ship_dim.name,
                        ship_dim.callsign,
                        ship_dim.width,
                        ship_dim.length,
                        ship_dim.type_of_position_fixing_device as fixing_device,
                        ship_type_dim.ship_type,
                        nav_dim.navigational_status,
                        data_fact.location as df_loc1,
                        data_fact.time_id as df_loc1_time_id,
                        data_fact.sog as df_loc1_sog,
                        ST_Distance(ST_Transform(data_fact.location,3857), ST_Transform(result_seg_1.p1,3857)) / 0.5399 as dist_df_loc1_c1
                FROM result_seg_1 
                JOIN data_fact 
                ON (result_seg_1.id1 = data_fact.simplified_trip_id)
                NATURAL JOIN ship_dim
                NATURAL JOIN ship_type_dim
                NATURAL JOIN nav_dim
                WHERE ST_Equals(
                                data_fact.location,
                                ST_ReducePrecision(ST_StartPoint(seg1), 0.0001)
                            ) {filter_ship_type} {filter_nav_stats} 
            ),
            get_data_2 AS (
                SELECT DISTINCT on (data_fact.simplified_trip_id)
                        result_seg_2.id2 as simplified_trip_id,
                        data_fact.location as df_loc2, 
                        data_fact.time_id as df_loc2_time_id,
                        data_fact.sog as df_loc2_sog,
                        ST_Distance(ST_Transform(data_fact.location,3857), ST_Transform(result_seg_2.p2,3857)) / 0.5399 as dist_df_loc2_c2
                FROM result_seg_2 JOIN data_fact ON (result_seg_2.id2 = data_fact.simplified_trip_id)
                WHERE ST_Equals(
                            data_fact.location,
                            ST_ReducePrecision(ST_StartPoint(seg2), 0.0001)
                )
            )
            SELECT gd1.simplified_trip_id, gd1.line_string, gd1.mmsi, gd1.type_of_mobile, 
                gd1.imo, gd1.name, gd1.callsign, gd1.width, gd1.length, gd1.fixing_device,
                gd1.ship_type, gd1.navigational_status,
                gd1.df_loc1, gd1.df_loc1_time_id, gd1.df_loc1_sog, gd1.dist_df_loc1_c1, 
                gd2.df_loc2, gd2.df_loc2_time_id, gd2.df_loc2_sog, gd2.dist_df_loc2_c2
            FROM get_data_1 as gd1 
            JOIN get_data_2 as gd2 
            ON (gd1.simplified_trip_id = gd2.simplified_trip_id);'''

def get_line_strings(poly1: GridPolygon, poly2: GridPolygon, filter: Filter, logger: Logger) -> pd.DataFrame:
    sql_query = query_line_strings_and_data_for_ETA(filter)
    # print(sql_query)
    df = gpd.read_postgis(
            sql_query, 
            engine, 
            params=
            {
                "centroid1": poly1.centroid,
                "centroid2": poly2.centroid,
                "poly1": wkb.dumps(poly1.polygon, hex=True, srid=4326), 
                "poly2": wkb.dumps(poly2.polygon, hex=True, srid=4326)
            },
            geom_col='line_string'
        )

    if len(df) == 0:
        logger.warning('No trips were found for the selected polygons')
        raise HTTPException(status_code=404, detail='No trips were found for the selected polygons')

    return df