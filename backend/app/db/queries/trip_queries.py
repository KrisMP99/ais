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


def fetch_closets_points_to_centroid():
    return '''WITH centroids_linestrings AS (
                SELECT
                    DISTINCT std.line_string as line_string, std.simplified_trip_id as simplified_id, 
                    ST_ClosestPoint(ST_GeomFromEWKT(%(centroid1)s), line_string) as p1, 
                    ST_ClosestPoint(ST_GeomFromEWKT(%(centroid2)s), line_string) as p2
                FROM
                    simplified_trip_dim AS std
                WHERE
                    ST_Intersects(
                        std.line_string,
                        ST_GeomFromEWKT(%(poly1)s)
                    ) AND
                    ST_Intersects(
                        std.line_string,
                        ST_GeomFromEWKT(%(poly2)s)
                    )
            ),
                segments AS (
                    SELECT simplified_trip_id, centroids_linestrings.p1, centroids_linestrings.p2, centroids_linestrings.line_string as line_string,
                            ST_MakeLine(
                                        lag((pt).geom, 1, NULL) 
                                        OVER (
                                                PARTITION BY simplified_trip_id 
                                                ORDER BY simplified_trip_id, (pt).path), (pt).geom
                                            ) AS geom
                FROM (
                    SELECT simplified_trip_id, ST_DumpPoints(simplified_trip_dim.line_string) AS pt 
                    FROM simplified_trip_dim 
                    WHERE simplified_trip_dim.simplified_trip_id IN (SELECT simplified_id FROM centroids_linestrings)
                ) as dumps,
                centroids_linestrings
            ), 
            line_result_segments as (
                SELECT line_string,
                    (
                        SELECT geom as segment1
                        FROM segments
                        WHERE ST_Intersects(segments.p1, geom)
                    ), 
                    (
                        SELECT geom as segment2
                        FROM segments
                        WHERE ST_Intersects(segments.p2, geom)
                    )
                FROM segments
                WHERE segments.geom IS NOT NULL
            ),
            points as (
                SELECT ST_StartPoint(segment1) as point1, ST_StartPoint(segment2) as point2, line_string
                FROM line_result_segments
            )
            SELECT data_fact.data_fact_id, data_fact.location as location, line_string
            FROM data_fact, points
            WHERE ST_Equals(point1, data_fact.location) OR ST_Equals(point2, data_fact.location)'''


def query_fetch_line_strings_given_polygon() -> str:
    # We select all line strings that intersect with the two hexagons
    return '''
            SELECT
                DISTINCT ON (std.simplified_trip_id) std.line_string as line_string, std.simplified_trip_id, 
                sd.mmsi, sd.type_of_mobile, sd.imo, sd.name, sd.width, sd.length, 
                ship_type_dim.ship_type,
                ST_ClosestPoint(ST_GeomFromEWKT(%(centroid1)s), line_string) as p1, 
                ST_ClosestPoint(ST_GeomFromEWKT(%(centroid2)s), line_string) as p2
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
                "centroid1": poly1.centroid,
                "centroid2": poly2.centroid,
                "poly1": wkb.dumps(poly1.polygon, hex=True, srid=4326), 
                "poly2": wkb.dumps(poly2.polygon, hex=True, srid=4326)
            },
            geom_col='line_string'
        )
    
    print(df.columns)
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





# WIP QUERY!
'''
WITH centroids_linestrings AS (
	SELECT
		DISTINCT ON (std.simplified_trip_id)
		std.line_string as line_string, std.simplified_trip_id as simplified_id, 
		ST_ClosestPoint(line_string, ST_GeomFromEWKT('0101000020E610000011EE842C424A25407B54ECE2FBDA4C40')) as p1, 
		ST_ClosestPoint(line_string, ST_GeomFromEWKT('0101000020E61000008DF762C53F8F2540EB96F1E24CE04C40')) as p2
	FROM
		simplified_trip_dim AS std
	WHERE
		ST_Intersects(std.line_string, ST_GeomFromEWKT('0103000020E6100000010000000700000067929BC6431C25407B54ECE2FBDA4C403B4090F94233254097A4BF52A9D54C40E59B795F4161254097A4BF52A9D54C40B9496E92407825407B54ECE2FBDA4C40E59B795F41612540EA96F1E24CE04C403B4090F942332540EA96F1E24CE04C4067929BC6431C25407B54ECE2FBDA4C40'))
		AND
		ST_Intersects(std.line_string, ST_GeomFromEWKT('0103000020E61000000100000007000000E59B795F41612540EA96F1E24CE04C40B9496E92407825407B54ECE2FBDA4C4064A557F83EA625407B54ECE2FBDA4C4038534C2B3EBD2540EA96F1E24CE04C4064A557F83EA62540AE1E16539CE54C40B9496E9240782540AE1E16539CE54C40E59B795F41612540EA96F1E24CE04C40'))
),
segments AS (
	SELECT dumps.simplified_id, dumps.p1, dumps.p2, dumps.line_string as line_string, dumps.c2,
			ST_MakeLine(
						lag((pt).geom, 1, NULL) 
						OVER (
								PARTITION BY dumps.simplified_id 
								ORDER BY dumps.simplified_id, (pt).path), (pt).geom
							) AS geom
	FROM (
		SELECT centroids_linestrings.simplified_id, centroids_linestrings.p1, 
			   centroids_linestrings.p2, centroids_linestrings.line_string,
			   ST_DumpPoints(centroids_linestrings.line_string) AS pt 
		FROM centroids_linestrings 
	) as dumps

),
result_seg_1 AS (
	SELECT DISTINCT ON (simplified_id) simplified_id as id1, segments.geom as seg1, segments.p1 as p1
	FROM segments
	WHERE ST_DWithin(ST_Transform(segments.p1, 3857), ST_Transform(segments.geom, 3857), 100)
),
result_seg_2 AS (
	SELECT DISTINCT ON (simplified_id) simplified_id as id2, segments.geom as seg2, segments.p2 as p2
	FROM segments
	WHERE ST_DWithin(ST_transform(segments.p2, 3857), ST_Transform(segments.geom, 3857), 100)
),
get_data_1 AS (
	SELECT DISTINCT on (data_fact.location) data_fact.data_fact_id as id1, data_fact.location as loc1, seg1, result_seg_1.simplified_id as simplified_id_1
	FROM result_seg_1 JOIN data_fact ON (result_seg_1.simplified_id = data_fact.simplified_trip_id)
	WHERE ST_Equals(
				data_fact.location,
				ST_ReducePrecision(ST_StartPoint(seg1), 0.0001)
	)
),
get_data_2 AS (
	SELECT DISTINCT on (data_fact.location) data_fact.data_fact_id as id2, data_fact.location as loc2, seg2, result_seg_2.simplified_id as simplified_id_2
	FROM result_seg_2 JOIN data_fact ON (result_seg_2.simplified_id = data_fact.simplified_trip_id)
	WHERE ST_Equals(
				data_fact.location,
				ST_ReducePrecision(ST_StartPoint(seg2), 0.0001)
	)
)


'''