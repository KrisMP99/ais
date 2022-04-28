from dotenv import load_dotenv
import psycopg2
import os
import configparser
from pathlib import Path

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
HOST_DB = os.getenv('HOST_DB')
DB_NAME = os.getenv('DB_NAME')

hexagon_grid_resolutions = []
square_grid_resolutions = []

def setup_bounds() -> None:
    '''
    Setup the bounds used when generating the hexagon and square grids.
    Should only be run once initially, but if its run again it will redo the bounds all over again.
    '''
    print("Creating map_bounds...")
    with psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB) as conn:
        # First create our map_bounds table...
        sql_map_bounds_query = '''
                                CREATE TABLE IF NOT EXISTS map_bounds(
                                    country_name varchar,
                                    geom GEOMETRY
                                );
                               '''
        
        with conn.cursor() as cursor:
            cursor.execute(sql_map_bounds_query)

        # Truncate the table in case it already exists and has data in it (avoid duplicate data)
        with conn.cursor() as cursor:
            sql_truncate_table = "TRUNCATE TABLE map_bounds;"
            cursor.execute(sql_truncate_table)
        
        # Then copy the bounds from the 'map_bounds.csv'-file into our map_bounds table
        with conn.cursor() as cursor:
            path = Path(__file__)
            ROOT_DIR = path.parent.absolute()
            config_path = os.path.join(ROOT_DIR, "map_bounds.csv")

            with open(config_path, 'r') as f:
                sql_copy_query = f"COPY map_bounds \
                                FROM STDIN \
                                DELIMITER ',' \
                                CSV;"
                cursor.copy_expert(sql_copy_query, file=f)
        
        # And finally, we analyze the table
        with conn.cursor() as cursor:
            sql_analyze_query = "ANALYZE map_bounds;"
            cursor.execute(sql_analyze_query)
    print("Finished with map_bounds")


def create_tables_for_grids(hexagons = True) -> None:
    '''
    Creates the TABLES used to store the grids for either hexagons or squares.
    It uses the resoultions (side lenghts) given in the `grid_setup_config.ini`-file.
    :param hexagons: If set to true, it will generates the tables for the hexagons. If false, it will generate tables for square grids instead. Default: True
    '''
    if hexagons:
        dim_type = "hex"
        resolutions = hexagon_grid_resolutions
    else:
        dim_type = "square"
        resolutions = square_grid_resolutions

    with psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB) as conn:
        for dim_size in resolutions:
            sql_create_hexagon_table = f'''
                                            CREATE TABLE IF NOT EXISTS {dim_type}_{dim_size}_dim (
                                            {dim_type}_{dim_size}_row INTEGER, 
                                            {dim_type}_{dim_size}_column INTEGER,
                                            PRIMARY KEY({dim_type}_{dim_size}_row, {dim_type}_{dim_size}_column),
                                            centroid GEOMETRY(Point, 3857),
                                            grid_geom GEOMETRY);
                                       '''

            with conn.cursor() as cursor:
                cursor.execute(sql_create_hexagon_table)


def fill_and_convert_tables(hexagons = True) -> None:
    '''
    Generates grids on the form hexagons or squares, and insert it into the tables.
    This function requires, that the tables used to store the grids have already been created (see the `create_grids()`-function).
    It will generate the grid sizes according to the resolutions (side length) given in the `grid_setup_config.ini`-file.
    :param hexagons: If set to True, it will generate hexagons grids. If set to False, it will generate the square grids. Default: True
    '''
    if hexagons:
        dim_type = "hex"
        resolutions = hexagon_grid_resolutions
        grid_type = "ST_HexagonGrid"
        table_name = "hexes"
    else:
        dim_type = "square"
        resolutions = square_grid_resolutions
        grid_type = "ST_SquareGrid"
        table_name = "squares"

    with psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB) as conn:
        for dim_size in resolutions:
            size = int(dim_size)
            sql_fill_hexagons = f'''
                                    INSERT INTO {dim_type}_{dim_size}_dim({dim_type}_{dim_size}_row, {dim_type}_{dim_size}_column, centroid, grid_geom)
                                    SELECT {table_name}.j, {table_name}.i, ST_centroid({table_name}.geom), {table_name}.geom  
                                    FROM {grid_type}({size}, ST_SetSRID(ST_EstimatedExtent('map_bounds','geom'), 3857)) AS {table_name}  
                                    INNER JOIN map_bounds as mb
                                    ON ST_Intersects(mb.geom, {table_name}.geom)
                                    AND mb.country_name = 'AREA_BOUNDS';
                                '''

            # Fill the hexagon grid inside our own defined bounds
            with conn.cursor() as cursor:
                cursor.execute(sql_fill_hexagons)
            
            # Remove all the hexagons which are inside of any of the countries
            delete_intersecting_geoms = f'''
                                                DELETE FROM {dim_type}_{dim_size}_dim
                                                WHERE grid_geom IN (
                                                    SELECT {dim_type}_{dim_size}_dim.grid_geom
                                                    FROM {dim_type}_{dim_size}_dim
                                                    INNER JOIN map_bounds as mb
                                                    ON ST_Within(grid_geom, mb.geom)
                                                    AND mb.country_name = 'ALL_COUNTRIES'
                                                );
                                            '''
            with conn.cursor() as cursor:
                cursor.execute(delete_intersecting_geoms)

            sql_transform_geom_to_4326 = f"ALTER TABLE {dim_type}_{dim_size}_dim ALTER COLUMN grid_geom TYPE Geometry(Point, 4326) USING ST_TRANSFORM(grid_geom, 4326)"
            with conn.cursor() as cursor:
                cursor.execute(sql_transform_geom_to_4326)
            
            sql_transform_centroid_to_4326 = f"ALTER TABLE {dim_type}_{dim_size}_dim ALTER COLUMN centroid TYPE Geometry(Point, 4326) USING ST_TRANSFORM(centroid, 4326)"
            with conn.cursor() as cursor:
                cursor.execute(sql_transform_centroid_to_4326)

def read_grids_resolutions_from_config_file() -> None:
    '''
    Reads the grid resolutions from the `grid_setup_config.ini`-file, and stores them in memory to be used later.
    '''
    path = Path(__file__)
    ROOT_DIR = path.parent.parent.absolute()
    config_path = os.path.join(ROOT_DIR, "grid_setup_config.ini")

    config = configparser.ConfigParser()
    config.read(config_path)
    hex_str_dims = config.get('HEXAGON', 'DIMENSIONS')
    square_str_dims = config.get('SQUARE', 'DIMENSIONS')
    
    hex_str_split = hex_str_dims.split(',')
    dim: str
    for dim in hex_str_split:
        if dim:
            hexagon_grid_resolutions.append(dim.strip())
    
    square_str_split = square_str_dims.split(',')
    for dim in square_str_split:
        if dim:
            square_grid_resolutions.append(dim.strip())

def truncate_grid_tables() -> None:
    '''
    Truncates both the hexagon and square grid tables (according to the resolutions `grid_setup_config.ini`-file).
    Requies the `read_grids_resolutions_from_config_file()` to be run first.
    '''
    with psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB) as conn:
        for dim_size in hexagon_grid_resolutions:
            sql_truncate_hex_query = f"TRUNCATE TABLE hex_{dim_size}_dim;"

            with conn.cursor() as cursor:
                cursor.execute(sql_truncate_hex_query)
        
        for dim_size in square_grid_resolutions:
            sql_truncate_square_query = f"TRUNCATE TABLE square_{dim_size}_dim;"
            
            with conn.cursor() as cursor:
                cursor.execute(sql_truncate_square_query)


def create_spatial_indexes() -> None:
    '''
    Creates spatial indexes for both the hexagon and square dimension tables (according to the grid resolutions given in the `grid_setup_config.ini`-file)
    Requries the tables to already exists, or the function `create_grids()` to be run atleast once, first.
    '''
    with psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB) as conn:
        for dim_size in hexagon_grid_resolutions:
            sql_hex_idx_query = f"CREATE INDEX hex_{dim_size}_dim_idx ON hex_{dim_size}_dim USING GIST(grid_geom);"

            with conn.cursor() as cursor:
                cursor.execute(sql_hex_idx_query)
        
        for dim_size in square_grid_resolutions:
            sql_square_idx_query = f"CREATE INDEX sqaure_{dim_size}_dim_idx ON square_{dim_size}_dim USING GIST(grid_geom);"
        
            with conn.cursor() as cursor:
                cursor.execute(sql_square_idx_query)


def vacuum_and_analyze_tables():
    '''
    Vacuums and analyzes all the tables in the database.
    Should be run once after inserting/updating a lot of rows in a table (i.e., it should be run once everytime we have processed and inserted a .CSV file)
    '''
    with psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB) as conn:
        with conn.cursor() as cursor:
            sql_query = "VACUUM ANALYZE;"
            cursor.execute(sql_query)


def create_star_schema() -> None:
    '''
    Creates the star schema along with spatial indexes on the `location` column.
    Requires the `read_grids_resolutions_from_config_file()` to be run first.
    '''
    result = []

    for dim_size in hexagon_grid_resolutions:
        size = dim_size.strip()
        grid_col_name = f"hex_{size}_column INTEGER"
        grid_row_name = f"hex_{size}_row INTEGER"
        result.append(grid_col_name)
        result.append(grid_row_name)
    
    for dim_size in square_grid_resolutions:
        size = dim_size.strip()
        grid_col_name = f"square_{size}_column INTEGER"
        grid_row_name = f"square_{size}_row INTEGER"
        result.append(grid_col_name)
        result.append(grid_row_name)

    result_str = ",".join(result)
    result_str += ","

    foregin_keys = []
    for dim_size in hexagon_grid_resolutions:
        size = dim_size.strip()
        constraint = f'''CONSTRAINT fk_hex_{size} 
                         FOREIGN KEY (hex_{size}_column, hex_{size}_row) 
                         REFERENCES hex_{size}_dim(hex_{size}_column, hex_{size}_row)'''
        foregin_keys.append(constraint)

    for dim_size in square_grid_resolutions:
        size = dim_size.strip()
        constraint = f'''CONSTRAINT fk_square_{size} 
                         FOREIGN KEY (square_{size}_column, square_{size}_row) 
                         REFERENCES square_{size}_dim(square_{size}_column, square_{size}_row)'''
        foregin_keys.append(constraint)

    foregin_keys_str = ",".join(foregin_keys)
    

    sql_star_schema = f'''
                            CREATE TABLE IF NOT EXISTS date_dim(
                                date_id INTEGER PRIMARY KEY,
                                date DATE,
                                year INTEGER,
                                month INTEGER,
                                day INTEGER
                            );

                            CREATE TABLE IF NOT EXISTS time_dim(
                                time_id INTEGER PRIMARY KEY,
                                time TIME WITHOUT TIME ZONE,
                                hour INTEGER,
                                quarter_hour INTEGER,
                                five_minutes INTEGER
                            );

                            CREATE TABLE IF NOT EXISTS ship_dim(
                                ship_id INTEGER PRIMARY KEY,
                                mmsi INTEGER,
                                type_of_mobile VARCHAR,
                                imo INTEGER,
                                name VARCHAR,
                                callsign VARCHAR,
                                type_of_position_fixing_device VARCHAR,
                                width smallint,
                                length smallint
                            );

                            CREATE TABLE IF NOT EXISTS ship_type_dim(
                                ship_type_id INTEGER PRIMARY KEY,
                                ship_type varchar
                            );

                            CREATE TABLE IF NOT EXISTS nav_dim(
                                nav_id INTEGER PRIMARY KEY,
                                navigational_status VARCHAR
                            );

                            CREATE TABLE IF NOT EXISTS trip_dim(
                                trip_id INTEGER PRIMARY KEY,
                                line_string GEOMETRY(linestring, 4326)
                            );

                            create table IF NOT EXISTS simplified_trip_dim(
                                simplified_trip_id INTEGER PRIMARY KEY,
                                line_string GEOMETRY(linestring, 4326)
                            );

                            CREATE TABLE IF NOT EXISTS data_fact (
                                data_fact_id SERIAL PRIMARY KEY,
                                date_id INTEGER REFERENCES date_dim(date_id),
                                time_id INTEGER REFERENCES time_dim(time_id),
                                ship_type_id INTEGER REFERENCES ship_type_dim(ship_type_id),
                                ship_id INTEGER REFERENCES ship_dim(ship_id),
                                nav_id INTEGER REFERENCES nav_dim(nav_id),
                                trip_id INTEGER REFERENCES trip_dim(trip_id),
                                simplified_trip_id INTEGER REFERENCES simplified_trip_dim(simplified_trip_id),
                                {result_str}
                                location GEOMETRY(point, 4326),
                                rot NUMERIC,
                                sog NUMERIC,
                                cog NUMERIC,
                                heading SMALLINT,
                                draught NUMERIC,
                                destination VARCHAR,
                                {foregin_keys_str}
                            );
                        '''
    with psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql_star_schema)
        with conn.cursor() as cursor:
            sql_data_fact_idx_query = f"CREATE INDEX data_fact_idx ON data_fact USING GIST(location);"
            cursor.execute(sql_data_fact_idx_query)
    

setup_bounds()
read_grids_resolutions_from_config_file()
create_tables_for_grids(hexagons=True)
create_tables_for_grids(hexagons=False)
fill_and_convert_tables(hexagons=True)
fill_and_convert_tables(hexagons=False)
create_spatial_indexes()
create_star_schema()


