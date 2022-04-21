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

hexagon_grid_resolutions = [str]
square_grid_resolutions = [str]

def setup_bounds() -> None:
    '''
    Setup the bounds used when generating the hexagon and square grids.
    Should only be run once initially, but if ran again it will redo the bounds all over again.
    '''
    with psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB, port="5432") as conn:
        # First create our map_bounds table...
        sql_map_bounds_query = '''
                                CREATE TABLE map_bounds(
                                    country_name varchar,
                                    geom GEOMETRY(MULTIPOLYGON, 4326)
                                );
                               '''
        with conn.cursor() as cursor:
            cursor.execute(sql_map_bounds_query)

        # Then copy the bounds from the 'map_bounds.csv'-file into our map_bounds table
        with conn.cursor() as cursor:
            path = Path(__file__)
            ROOT_DIR = path.parent.absolute()
            config_path = os.path.join(ROOT_DIR, "map_bounds.csv")

            sql_copy_query = f"COPY map_test \
                               FROM {config_path}\
                               DELIMITER ','\
                               CSV;"
            cursor.execute(sql_copy_query)
        
        # Insert our own bounds, otherwise it would generate grids covering the entire globe
        with conn.cursor() as cursor:
            sql_DK_SEA_query = "INSERT INTO map_bounds(country_name, geom) VALUES('DK_BOUNDS','POLYGON((3.24 58.35, 3.24 53.32, 16.49 53.32, 16.49 56.23, 13.31 56.68, 10.97 60.03, 7.48 58.35, 3.24 58.35))');"
            cursor.execute(sql_DK_SEA_query)
        
        # We convert the table to SRID 3857, so we can use meters instead of degrees
        with conn.cursor() as cursor:
            sql_convert_query = "ALTER TABLE map_bounds ALTER COLUMN geom TYPE Geometry(MultiPolygon, 3857) USING ST_Transform(geom, 3857);"
            cursor.execute(sql_convert_query)
        
        # And finally, we analyze the table
        with conn.cursor() as cursor:
            sql_analyze_query = "SQL ANALYZE map_bounds;"
            cursor.execute(sql_analyze_query)


def create_hexagon_grids() -> None:
    with psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB, port="5432") as conn:
        for dim_size in hexagon_grid_resolutions:
            sql_create_hexagon_table = f'''
                                            CREATE TABLE hex_{dim_size}_dim (
                                            hex_{dim_size}_row INTEGER, 
                                            hex_{dim_size}_column INTEGER, 
                                            PRIMARY KEY(hex_{dim_size}_row, hex_{dim_size}_column), 
                                            hexagon geometry);
                                       '''
            with conn.cursor() as cursor:
                cursor.execute(sql_create_hexagon_table)

def create_square_grids() -> None:
    with psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB, port="5432") as conn:
        for dim_size in hexagon_grid_resolutions:
            sql_create_hexagon_table = f'''
                                            CREATE TABLE square_{dim_size}_dim (
                                            square_{dim_size}_row INTEGER, 
                                            square_{dim_size}_column INTEGER, 
                                            PRIMARY KEY(square_{dim_size}_row, square_{dim_size}_column), 
                                            hexagon geometry);
                                       '''
            with conn.cursor() as cursor:
                cursor.execute(sql_create_hexagon_table)


def fill_hexagons_tables() -> None:
    with psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB, port="5432") as conn:
        for dim_size in hexagon_grid_resolutions:
            size = int(dim_size)
            sql_fill_hexagons = f'''
                                    INSERT INTO hex_{dim_size}_dim(hex_{dim_size}_row, hex_{dim_size}_column, hexagon)
                                    SELECT hexes.j, hexes.i, hexes.geom  
                                    FROM ST_HexagonGrid({size}, ST_SetSRID(ST_EstimatedExtent('map_bounds','geom'), 3857)) AS hexes  
                                    INNER JOIN map_bounds AS MB ON ST_Intersects(mb.geom, hexes.geom)
                                    WHERE MB.country_name = 'DK_BOUNDS';
                                '''
            # Fill the hexagon grid inside our own defined bounds
            with conn.cursor() as cursor:
                cursor.execue(sql_fill_hexagons)
            
            # Remove all the hexagons which are inside of any of the countries
            sql_delete_hexagons = f'''
                                   SELECT hex_{dim_size}_row, hex_{dim_size}_column, hexagon
                                   FROM hex_{dim_size}_dim
                                   WHERE 
                                   '''
            with conn.cursor() as cursor:
                cursor.execue(sql_fill_hexagons)
            

def read_grids_resolutions_from_config_file() -> None:
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
            hexagon_grid_resolutions.append(dim)
    
    square_str_split = square_str_dims.split(',')
    for dim in square_str_split:
        if dim:
            square_grid_resolutions.append(dim)

def add_hexagon_grid_resolution(resolution: int) -> None:
    '''
    Adds a resolution to the hexagon grid.
    Example: If resolution = 500, a hexagon grid with a radius of 500 meters will be created
    along with an spatial index.
    :param resolution: The resolution of the hexagon grid
    '''

    hexagon_grid_resolutions.append(resolution)

def add_square_grid_resolution(resolution: int) -> None:
    '''
    Adds a resolution to the square grid.
    Example: If resolution = 500, a square grid with a radius of 500 meters will be created
    along with an spatial index.
    :param resolution: The resolution of the square grid
    '''
    square_grid_resolutions.append(resolution)


def create_hexagon_grid(resolutions: list[int]) -> None:
    with psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB, port="5432") as conn:
        with conn.cursor() as cursor:
            print()
