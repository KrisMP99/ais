THRESHOLD = 1000

def execute_line_strings(cursor, conn, trip_id: int):
    '''
    Generates the both the 'normal' line strings and simplified line strings for each trip.
    It will also update the data_fact table to update the simplified_trip_id
    :param cursor: The cursor used to execute the SQL
    :trip_id: The trip id to begin from.
    '''


    sql_drop_trip_temp_table = "DROP TABLE IF EXISTS line_temp;"
    sql_trip_table_insert_query = f'''
                                    WITH trip_list AS (
                                        SELECT trip_id, ST_MakeLine(array_agg(location ORDER BY time_id ASC)) as line
                                        FROM data_fact
                                        WHERE trip_id >= {trip_id}
                                        GROUP BY trip_id 
                                    )
                                    SELECT trip_id, line
                                    INTO UNLOGGED TABLE line_temp
                                    FROM trip_list;
                                    '''
    sql_trip_update_query = f'''
                             UPDATE trip_dim
                             SET line_string = line
                             FROM line_temp
                             WHERE line_temp.trip_id = trip_dim.trip_id;
                             '''
    cursor.execute(sql_drop_trip_temp_table)
    conn.commit()
    cursor.execute(sql_trip_table_insert_query)
    conn.commit()
    cursor.execute(sql_trip_update_query)
    conn.commit()
    cursor.execute(sql_drop_trip_temp_table)
    conn.commit()

    sql_drop_simplified_trip_table = "DROP TABLE IF EXISTS line_simplified_temp;"
    sql_simplified_trip_table_insert_query = f'''
                                            WITH simplified_trip_list AS (
                                                SELECT trip_id, ST_Simplify(ST_Transform(line_string, 3857), {THRESHOLD}) as line
                                                FROM trip_dim
                                                WHERE trip_id >= {trip_id}
                                                GROUP BY trip_id 
                                            )

                                            SELECT trip_id, ST_Transform(line, 4326) as line_simplified
                                            INTO UNLOGGED TABLE line_simplified_temp
                                            FROM simplified_trip_list;
                                            '''
    sql_simplified_trip_update_query = f'''
                                            UPDATE simplified_trip_dim
                                            SET line_string = line_simplified
                                            FROM line_simplified_temp
                                            WHERE line_simplified_temp.trip_id = simplified_trip_dim.simplified_trip_id;
                                        '''
    cursor.execute(sql_drop_simplified_trip_table)
    conn.commit()
    cursor.execute(sql_simplified_trip_table_insert_query)
    conn.commit()
    cursor.execute(sql_simplified_trip_update_query)
    conn.commit()
    cursor.execute(sql_drop_simplified_trip_table)
    conn.commit()

    sql_drop_simplified_data_points = "DROP TABLE IF EXISTS data_points;"
    sql_simplified_data_points_query = f'''
                                            WITH simplified_trips AS (
                                            SELECT simplified_trip_dim.simplified_trip_id, simplified_trip_dim.line_string, data_fact.data_fact_id
                                            FROM simplified_trip_dim JOIN data_fact
                                            ON simplified_trip_dim.simplified_trip_id = data_fact.trip_id
                                            WHERE data_fact.trip_id >= {trip_id} AND ST_intersects(data_fact.location, line_string)
                                            )

                                            SELECT data_fact_id, simplified_trip_id
                                            INTO UNLOGGED TABLE data_points
                                            FROM simplified_trips;
                                        '''
    sql_update_data_fact_simplified_trip_ids = f'''
                                                    UPDATE data_fact
                                                    SET simplified_trip_id = data_points.simplified_trip_id
                                                    FROM data_points
                                                    WHERE data_points.data_fact_id = data_fact.data_fact_id;
                                                '''

    sql_drop_simplified_data_points = "DROP TABLE IF EXISTS simplified_points_temp;"
    sql_simplified_data_points_query = f'''
                                            WITH points_in_trip AS (
                                            SELECT simplified_trip_id, (ST_DumpPoints(line_string)).geom as point
                                            FROM simplified_trip_dim
                                            WHERE simplified_trip_id >= {trip_id} 
                                            ),
                                            points_data_fact AS (
                                                SELECT data_fact_id, points_in_trip.simplified_trip_id as simplified_trip_id
                                                FROM points_in_trip JOIN data_fact
                                                ON points_in_trip.point = data_fact.location
                                                WHERE (points_in_trip.simplified_trip_id = data_fact.trip_id) AND (data_fact.trip_id >= {trip_id})

                                            )
                                            SELECT points_data_fact.data_fact_id, points_data_fact.simplified_trip_id
                                            INTO UNLOGGED TABLE simplified_points_temp
                                            FROM points_data_fact;
                                            '''

    sql_update_data_fact_simplified_trip_ids = f'''
                                                    UPDATE data_fact
                                                    SET simplified_trip_id = simplified_points_temp.simplified_trip_id
                                                    FROM simplified_points_temp
                                                    WHERE (simplified_points_temp.data_fact_id = data_fact.data_fact_id) AND (data_fact.trip_id >= {trip_id});
                                                '''
    
    cursor.execute(sql_drop_simplified_data_points)
    conn.commit()
    cursor.execute(sql_simplified_data_points_query)
    conn.commit()
    cursor.execute(sql_update_data_fact_simplified_trip_ids)
    conn.commit()
    cursor.execute(sql_drop_simplified_data_points)
    conn.commit()


def execute_hex_ids(cursor, conn, simplified_trip_id):
    sql_drop_500_hex_table = "DROP TABLE IF EXISTS temp_hex_500;"
    sql_hex_500_generate_query = f'''
                                        WITH hexes500 as (
                                            SELECT hex_500_dim.hex_500_row as hex5row, hex_500_dim.hex_500_column as hex5col, data_fact.data_fact_id as fact_id_500
                                            FROM hex_500_dim JOIN data_fact 
                                            ON ST_intersects(data_fact.location, hex_500_dim.hexagon) AND (data_fact.simplified_trip_id >= {simplified_trip_id})
                                        )

                                        SELECT fact_id_500, hex5row, hex5col
                                        INTO temp_hex_500
                                        FROM hexes500; '''
    sql_hex_500_update_query = f'''
                                UPDATE data_fact df
                                SET hex_500_row = hex5row,
                                hex_500_column = hex5col
                                FROM temp_hex_500
                                WHERE df.data_fact_id = temp_hex_500.fact_id_500;
                                '''

    cursor.execute(sql_drop_500_hex_table)
    conn.commit()
    cursor.execute(sql_hex_500_generate_query)
    conn.commit()
    cursor.execute(sql_hex_500_update_query)
    conn.commit()
    cursor.execute(sql_drop_500_hex_table)
    conn.commit()

    sql_drop_10000_hex_table = "DROP TABLE IF EXISTS temp_hex_10000;"
    sql_hex_10000_generate_query = f'''
                                        WITH hexes10000 as (
                                            SELECT hex_10000_dim.hex_10000_row as hex10row, hex_10000_dim.hex_10000_column as hex10col, data_fact.data_fact_id as fact_id_10000
                                            FROM hex_10000_dim JOIN data_fact 
                                            ON ST_intersects(data_fact.location, hex_10000_dim.hexagon) AND (data_fact.simplified_trip_id >= {simplified_trip_id})
                                        )

                                        SELECT fact_id_10000, hex10row, hex10col
                                        INTO temp_hex_10000
                                        from hexes10000; '''
    sql_hex_10000_update_query = f'''
                                UPDATE data_fact df
                                SET hex_10000_row = hex10row,
                                hex_10000_column = hex10col
                                FROM temp_hex_10000
                                WHERE df.data_fact_id = temp_hex_10000.fact_id_10000;
                                '''
    cursor.execute(sql_drop_10000_hex_table)
    conn.commit()
    cursor.execute(sql_hex_10000_generate_query)
    conn.commit()
    cursor.execute(sql_hex_10000_update_query)
    conn.commit()
    cursor.execute(sql_drop_10000_hex_table)
    conn.commit()

def vacuum_and_analyze_tables(cursor, conn, logger):
    sql_query = ""