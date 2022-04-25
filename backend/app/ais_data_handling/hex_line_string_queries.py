from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
HOST_DB = os.getenv('HOST_DB')
DB_NAME = os.getenv('DB_NAME')

def create_line_strings(trip_id: int, threshold:int):
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




    sql_drop_simplified_trip_table = "DROP TABLE IF EXISTS line_simplified_temp;"
    sql_simplified_trip_table_insert_query = f'''
                                            WITH simplified_trip_list AS (
                                                SELECT trip_id, ST_Simplify(ST_Transform(line_string, 3857), {threshold}) as line
                                                FROM trip_dim
                                                WHERE trip_id >= {trip_id}
                                                GROUP BY trip_id 
                                            )

                                            SELECT trip_id, ST_Transform(line, 4326) as line_simplified
                                            INTO UNLOGGED TABLE line_simplified_temp
                                            FROM simplified_trip_list;
                                            '''
    sql_simplified_trip_update_query = f'''
                                            INSERT INTO simplified_trip_dim(simplified_trip_id, line_string)
                                            SELECT trip_id, line_simplified
                                            FROM line_simplified_temp
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

    
    with psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB) as conn:
        with conn.cursor() as cursor:
                cursor.execute(sql_drop_trip_temp_table)
        with conn.cursor() as cursor:
                cursor.execute(sql_trip_table_insert_query)
        with conn.cursor() as cursor:
                cursor.execute(sql_trip_update_query)
        with conn.cursor() as cursor:
                cursor.execute(sql_drop_trip_temp_table)

        with conn.cursor() as cursor:
                cursor.execute(sql_drop_simplified_trip_table)
        with conn.cursor() as cursor:
                cursor.execute(sql_simplified_trip_table_insert_query)
        with conn.cursor() as cursor:
                cursor.execute(sql_simplified_trip_update_query)
        with conn.cursor() as cursor:
                cursor.execute(sql_drop_simplified_trip_table)
        
        with conn.cursor() as cursor:
                cursor.execute(sql_drop_simplified_data_points)
        with conn.cursor() as cursor:
                cursor.execute(sql_simplified_data_points_query)
        with conn.cursor() as cursor:
                cursor.execute(sql_update_data_fact_simplified_trip_ids)
        with conn.cursor() as cursor:
                cursor.execute(sql_drop_simplified_data_points)



def create_hex_ids(square_resolutions, hex_resolutions, simplified_trip_id):
    with psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB) as conn:
        dim_str: str
        for dim_str in square_resolutions:
            dim_size_str = dim_str.strip()
            sql_drop_square_table = f"DROP TABLE IF EXISTS temp_square_{dim_size_str};"
            sql_square_generate_query = f'''
                                                WITH squares{dim_size_str} as (
                                                    SELECT square_{dim_size_str}_dim.square_{dim_size_str}_row as square_row, square_{dim_size_str}_dim.square_{dim_size_str}_column as square_col, data_fact.data_fact_id as fact_id_square
                                                    FROM square_{dim_size_str}_dim JOIN data_fact 
                                                    ON ST_Within(data_fact.location, square_{dim_size_str}_dim.grid_geom) 
                                                    AND (data_fact.simplified_trip_id >= {simplified_trip_id})
                                                )

                                                SELECT fact_id_square, square_row, square_col
                                                INTO temp_square_{dim_size_str}
                                                FROM squares{dim_size_str}; '''
            sql_square_update_query = f'''
                                        UPDATE data_fact df
                                        SET square_{dim_size_str}_row = square_row,
                                        square_{dim_size_str}_column = square_col
                                        FROM temp_square_{dim_size_str}
                                        WHERE df.data_fact_id = temp_square_{dim_size_str}.fact_id_square
                                    '''
            with conn.cursor() as cursor:
                cursor.execute(sql_drop_square_table)
            with conn.cursor() as cursor:
                cursor.execute(sql_square_generate_query)
            with conn.cursor() as cursor:
                cursor.execute(sql_square_update_query)
            with conn.cursor() as cursor:
                cursor.execute(sql_drop_square_table)
        
        for dim_str in hex_resolutions:
            dim_size_str = dim_str.strip()
            sql_drop_hex_table = f"DROP TABLE IF EXISTS temp_hex_{dim_size_str};"
            sql_hex_generate_query = f'''
                                                WITH hexes{dim_size_str} as (
                                                    SELECT hex_{dim_size_str}_dim.hex_{dim_size_str}_row as hex_row, hex_{dim_size_str}_dim.hex_{dim_size_str}_column as hex_col, data_fact.data_fact_id as fact_id_hex
                                                    FROM hex_{dim_size_str}_dim JOIN data_fact 
                                                    ON ST_Within(data_fact.location, hex_{dim_size_str}_dim.grid_geom) 
                                                    AND (data_fact.simplified_trip_id >= {simplified_trip_id})
                                                )

                                                SELECT fact_id_hex, hex_row, hex_col
                                                INTO temp_hex_{dim_size_str}
                                                FROM hexes{dim_size_str}; '''
            sql_hex_update_query = f'''
                                        UPDATE data_fact df
                                        SET hex_{dim_size_str}_row = hex_row,
                                        hex_{dim_size_str}_column = hex_col
                                        FROM temp_hex_{dim_size_str}
                                        WHERE df.data_fact_id = temp_hex_{dim_size_str}.fact_id_hex
                                    '''
            with conn.cursor() as cursor:
                cursor.execute(sql_drop_hex_table)
            with conn.cursor() as cursor:
                cursor.execute(sql_hex_generate_query)
            with conn.cursor() as cursor:
                cursor.execute(sql_hex_update_query)
            with conn.cursor() as cursor:
                cursor.execute(sql_drop_hex_table)


def vacuum_and_analyze_tables():
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    import sqlalchemy

    db_string = f"postgresql://{USER}:{PASS}@{HOST_DB}/{DB_NAME}"
    engine = sqlalchemy.create_engine(db_string)
    connection = engine.raw_connection()
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = connection.cursor()
    cursor.execute("VACUUM ANALYZE;")
    cursor.close()