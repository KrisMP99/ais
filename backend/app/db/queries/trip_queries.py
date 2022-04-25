from fastapi import HTTPException
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
                    h.{grid_type}_{size}_column, h.{grid_type}_{size}_row, h.grid_geom AS geom, ST_Transform(h.centroid, 4326) as centroid                                         
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



def query_fetch_line_strings_given_polygon() -> str:
    # We select all line strings that intersect with the two hexagons
    return '''
            SELECT
                std.line_string as line_string, std.simplified_trip_id
            FROM
                simplified_trip_dim AS std
            WHERE
                ST_Intersects(
                    std.line_string,
                    %(hex1)s::geometry
                ) AND
                ST_Intersects(
                    std.line_string,
                    %(hex2)s::geometry
                );
            '''
def query_get_points_in_line_string() -> str: 
    '''Select all points in the linestrings insecting the hexagons'''
    return  '''    
            SELECT
                std.simplified_trip_id, data_fact.hex_10000_row, 
                data_fact.hex_10000_column, data_fact.location, data_fact.time_id,
                data_fact.date_id, ship_type_dim.ship_type, data_fact.sog
            FROM
                data_fact
                INNER JOIN 
                    simplified_trip_dim AS std ON std.simplified_trip_id = data_fact.simplified_trip_id
                INNER JOIN
                    ship_type_dim ON ship_type_dim.ship_type_id = data_fact.ship_type_id    
            WHERE
                ST_Intersects(
                    std.line_string,
                    %(hex1)s::geometry
                ) AND
                ST_Intersects(
                    std.line_string,
                    %(hex2)s::geometry
                )
            GROUP BY 
                std.simplified_trip_id, data_fact.hex_10000_row, 
                data_fact.hex_10000_column, data_fact.location,
                data_fact.time_id, data_fact.date_id, 
                ship_type_dim.ship_type, data_fact.sog;
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