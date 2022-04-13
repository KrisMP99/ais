def query_fetch_hexagons_given_two_points() -> str:
    '''We find all hexagons where the points are found in'''
    return '''                                                         
                SELECT                                                          
                    h.column, h.row, h.geom                                            
                FROM                                                            
                    hex_10000_dim as h                           
                WHERE                                                           
                    ST_Within(
                        h.geom, ST_GeomFromWKB(%(p1)s::geometry, 3857)
                    ) OR     
                    ST_Within(
                        h.geom, ST_GeomFromWKB(%(p2)s::geometry, 3857)
                    );
            '''

def query_fetch_line_strings_given_hexagons() -> str:
    '''We select all line strings that intersect with the two hexagons'''
    return '''
            SELECT
                std.line_string
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
    # '''
    #         SELECT
    #             ST_AsGeoJSON(std.line_string)::json AS st_asgeojson
    #         FROM
    #             simplified_trip_dim AS std
    #         WHERE
    #             ST_Intersects(
    #                 ST_FlipCoordinates(std.line_string),
    #                 %(hex1geom)s::geometry
    #             ) AND
    #             ST_Intersects(
    #                 ST_FlipCoordinates(std.line_string),
    #                 %(hex2geom)s::geometry
    #             );
    #         '''