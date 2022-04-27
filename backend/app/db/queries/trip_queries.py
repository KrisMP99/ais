from logging import Logger
from fastapi import HTTPException
from shapely.geometry import Point
from app.models.grid_polygon import GridPolygon
import pandas as pd
import geopandas as gpd
import shapely.wkb as wkb
from app.db.database import engine, Session

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


def query_fetch_line_strings_given_polygon() -> str:
    # We select all line strings that intersect with the two hexagons
    return '''
            SELECT
                DISTINCT std.line_string as line_string, std.simplified_trip_id, sd.mmsi, sd.type_of_mobile, sd.imo, sd.name, sd.width, sd.length, ship_type_dim.ship_type
            FROM
                simplified_trip_dim AS std NATURAL JOIN data_fact as df NATURAL JOIN ship_dim as sd NATURAL JOIN ship_type_dim
            WHERE
                ST_Intersects(
                    std.line_string,
                    ST_GeomFromEWKT(%(poly1)s)
                ) AND
                ST_Intersects(
                    std.line_string,
                    ST_GeomFromEWKT(%(poly2)s)
                );
            '''
def get_line_strings(poly1: GridPolygon, poly2: GridPolygon, logger: Logger) -> pd.DataFrame:
    sql_query = query_fetch_line_strings_given_polygon()
    df = gpd.read_postgis(
            sql_query, 
            engine, 
            params=
            {
                "poly1": wkb.dumps(poly1.polygon, hex=True, srid=4326), 
                "poly2": wkb.dumps(poly2.polygon, hex=True, srid=4326)
            },
            geom_col='line_string'
        )
    
    print(df.head())
    if len(df) == 0:
        logger.warning('No trips were found for the selected polygons')
        raise HTTPException(status_code=404, detail='No trips were found for the selected polygons')

    return df

def query_get_points_in_line_string(simplified_trip_ids_array, poly_type, poly_size) -> str: 
    '''Select all points in the linestrings insecting the hexagons'''
    trips_to_select = "("
    for trip_id in simplified_trip_ids_array[:-1]:
        trips_to_select += f"{trip_id},"

    trips_to_select += f"{simplified_trip_ids_array[-1]})"

    return  f'''    
            SELECT
                data_fact.simplified_trip_id, data_fact.{poly_type}_{poly_size}_row as row, 
                data_fact.{poly_type}_{poly_size}_column as col, data_fact.location, data_fact.time_id,
                data_fact.date_id, data_fact.sog
            FROM data_fact
            WHERE data_fact.simplified_trip_id IN {trips_to_select}
            ORDER BY data_fact.time_id;
            '''

def get_points(simplified_trip_ids_array, poly_type, poly_size) -> pd.DataFrame:
    sql_query = query_get_points_in_line_string(simplified_trip_ids_array, poly_type, poly_size)
    df = gpd.read_postgis(
        sql_query, 
        engine,
        geom_col='location')
    return df


def query_point_exists_in_hexagon() -> str:
    return f'''
            {query_get_points_in_line_string()}
            SELECT
                date_dim.date_id, time_dim.time_id,
                data_fact.sog, pil.geom, ship_type_dim.ship_type,
                h.hex_10000_row, h.hex_10000_column

            FROM
                hex_10000_dim AS h, data_fact
                INNER JOIN date_dim ON date_dim.date_id = data_fact.date_id 
                INNER JOIN time_dim ON time_dim.time_id = data_fact.time_id
                INNER JOIN ship_type_dim ON ship_type_dim.ship_type_id = data_fact.ship_type_id
                INNER JOIN points_in_linestring AS pil ON pil.simplified_trip_id = data_fact.simplified_trip_id
            WHERE
                data_fact.location = pil.geom AND
                (
                    (ST_Within(
                            ST_FlipCoordinates(pil.geom),
                            ST_GeomFromWKB(%(hex1hex)s::geometry, 4326)
                    ) AND 
                    h.hex_10000_row = %(hex1row)s AND 
                    h.hex_10000_column = %(hex1column)s) OR
                    
                    (ST_Within(
                            ST_FlipCoordinates(pil.geom),
                            ST_GeomFromWKB(%(hex2hex)s::geometry, 4326)
                    ) AND 
                    h.hex_10000_row = %(hex2row)s AND 
                    h.hex_10000_column = %(hex2column)s)
                )
            ORDER BY time_dim.time_id
            '''