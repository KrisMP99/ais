from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
HOST_DB = os.getenv('HOST_DB')
DB_NAME = os.getenv('DB_NAME')


hexagon_grid_resolutions = list[int]
square_grid_resolutions = list[int]


def setup_bounds() -> None:
    '''
    Setup the bounds used when generating the hexagon and square grids.
    Should only be run once initially, but if ran again it will redo the bounds all over again.
    '''
    with psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB, port="5432") as conn:
        # First create our map_bounds table...


        # Then copy the bounds from the 'map_bounds.csv'-file into our map_bounds table
        with conn.cursor() as cursor:
            sql_query = "COPY map_test \
                         FROM 'C:\tmp\map_bounds.csv'\
                         DELIMITER ','\
                         CSV "
        print()
            


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
