def query_fetch_hexagons_given_two_points() -> str:
    '''We find all hexagons where the points are found in'''
    return '''                                                         
                SELECT                                                          
                    h.hex_10000_column, h.hex_10000_row, h.hexagon                                          
                FROM                                                            
                    hex_10000_dim as h                           
                WHERE                                                           
                    ST_Within(
                        %(p1)s::geometry, h.hexagon
                    ) OR     
                    ST_Within(
                        %(p2)s::geometry, h.hexagon
                    );
            '''

def query_fetch_line_strings_given_hexagons() -> str:
    # We select all line strings that intersect with the two hexagons
    return '''
            SELECT
                std.line_string
            FROM
                simplified_trip_dim AS std
            WHERE
                ST_Intersects(
                    ST_FlipCoordinates(std.line_string),
                    %(hex1)s::geometry
                ) AND
                ST_Intersects(
                    ST_FlipCoordinates(std.line_string),
                    %(hex2)s::geometry
                );
            '''
def query_get_points_in_line_string() -> str: 
    '''Select all points in the linestrings insecting the hexagons'''
    return  '''
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
                        ST_GeomFromWKB(%(hex1hex)s::geometry, 4326)
                    ) AND
                    ST_Intersects(
                        ST_FlipCoordinates(std.line_string),
                        ST_GeomFromWKB(%(hex2hex)s::geometry, 4326)
                    )
            )
            '''
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