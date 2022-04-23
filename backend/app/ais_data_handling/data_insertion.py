from venv import create
import numpy as np
from dotenv import load_dotenv
import psycopg2
import os
import pygrametl
from pygrametl.datasources import PandasSource
from pygrametl.tables import CachedDimension, BatchFactTable
from sqlalchemy import create_engine
import datetime
import geopandas as gpd
from shapely import wkb
import pandas as pd
from hex_line_string_queries import create_line_strings, create_hex_ids, vacuum_and_analyze_tables
import configparser
from pathlib import Path

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
HOST_DB = os.getenv('HOST_DB')
DB_NAME = os.getenv('DB_NAME')
COLUMNS = ['timestamp', 'type_of_mobile', 'mmsi', 'location','latitude','longitude', 'navigational_status', 'rot', 'sog', 'cog', 'heading', 'imo', 'callsign', 'name', 'ship_type', 'width', 'length', 'type_of_position_fixing_device', 'draught', 'destination', 'trip_id', 'simplified_trip_id']
cleansed_table_sql = "CREATE TABLE IF NOT EXISTS cleansed ( \
                      timestamp TIMESTAMP WITHOUT TIME ZONE,\
                      time TIME WITHOUT TIME ZONE, \
                      date DATE, \
                      year INTEGER, \
                      month INTEGER, \
                      day INTEGER, \
                      hour INTEGER, \
                      quarter_hour INTEGER, \
                      five_minutes INTEGER, \
                      date_id INTEGER, \
                      time_id INTEGER, \
                      type_of_mobile VARCHAR,\
                      mmsi integer,\
                      location GEOMETRY(point, 4326),\
                      navigational_status VARCHAR,\
                      rot numeric,\
                      sog numeric,\
                      cog numeric,\
                      heading smallint,\
                      imo integer,\
                      callsign VARCHAR,\
                      name VARCHAR,\
                      ship_type VARCHAR,\
                      width smallint,\
                      length smallint,\
                      type_of_position_fixing_device VARCHAR,\
                      draught numeric,\
                      destination VARCHAR,\
                      trip_id integer,\
                      simplified_trip_id integer, \
                      line_string INTEGER)" 

def calculate_date_tim_dim_and_hex(df: gpd.GeoDataFrame,logger):
    logger.info("Calculating attributes for date_dim and time_dim...")

    # Calculations for date_dim
    df['date'] = df['timestamp'].dt.date
    df['year'] = df['timestamp'].dt.year
    df['month'] = df['timestamp'].dt.month
    df['day'] = df['timestamp'].dt.day
    df['date_id'] = df['timestamp'].dt.strftime('%Y%m%d').astype(int)


    # Calculations for time_dim
    df['time_id'] = df['timestamp'].dt.strftime('%H%M%S').astype(int)
    df['time'] = df['timestamp'].dt.time
    df['hour'] = df['timestamp'].dt.hour
    df['quarter_hour'] = ((df['timestamp'] - df['timestamp'].dt.normalize()) / pd.Timedelta('15Min')).astype(int)
    df['five_minutes'] = ((df['timestamp'] - df['timestamp'].dt.normalize()) / pd.Timedelta('5Min')).astype(int)

    logger.info("Converting back to 4326...")
  
    df[['heading', 'width','length']] = df[['heading', 'width','length']].astype('Int16', errors='ignore')

    logger.info("Converting to hex...")
    df['location'] = df['location'].apply(lambda x: wkb.dumps(x, hex=True, srid=4326))
    
    df['line_string'] = None

    return df

def insert_trips(trip_df: gpd.GeoDataFrame, logger):
    db_string = f"postgresql://{USER}:{PASS}@{HOST_DB}/{DB_NAME}"
    engine = create_engine(db_string)
    logger.info("Inserting trips into 'trip_dim'")
    trip_df.to_postgis("trip_dim",con=engine, if_exists='append')
    logger.info("Finished inserting trips into 'trip_dim'")

def insert_simplified_trips(simplified_trip_df: gpd.GeoDataFrame, logger):
    db_string = f"postgresql://{USER}:{PASS}@{HOST_DB}/{DB_NAME}"
    engine = create_engine(db_string)
    simplified_trip_df = simplified_trip_df.drop(columns=['trip_id'])
    logger.info("Inserting simplified trips into 'simplified_trip_dim'")
    simplified_trip_df.to_postgis("simplified_trip_dim",con=engine, if_exists='append')
    logger.info("Finished inserting simplified trips into 'simplified_trip_dim'")


def convert_to_hex(row):
    row['location'] = wkb.dumps(row['location'], hex=True, srid=4326)


def get_resolutions_from_config_file(hexagons = True) -> str:
    path = Path(__file__)
    ROOT_DIR = path.parent.parent.absolute()
    db_path = os.path.join(ROOT_DIR, "db")
    config_path = os.path.join(db_path, 'grid_setup_config.ini')

    config = configparser.ConfigParser()
    config.read(config_path)
    if(hexagons):
        result = config.get('HEXAGON', 'DIMENSIONS')
    else:
        result = config.get('SQUARE', 'DIMENSIONS')

    return result

def insert_columns_for_grids(df: pd.DataFrame) -> pd.DataFrame:
    hex_str_dims = get_resolutions_from_config_file(hexagons=True).split(',')
    square_str_dims = get_resolutions_from_config_file(hexagons=False).split(',')

    for dim_size in hex_str_dims:
        size = dim_size.strip()
        grid_col_name = f"hex_{size}_column"
        grid_row_name = f"hex_{size}_row"

        df[[grid_col_name,grid_row_name]] = None
    
    for dim_size in square_str_dims:
        size = dim_size.strip()
        grid_col_name = f"square_{size}_column"
        grid_row_name = f"square_{size}_row"

        df[[grid_col_name,grid_row_name]] = None

    return df

def get_fact_table_key_refs() -> str:
    hex_str_dims = get_resolutions_from_config_file(hexagons=True).split(',')
    square_str_dims = get_resolutions_from_config_file(hexagons=False).split(',')

    result = ['date_id','time_id','ship_type_id','ship_id','nav_id','trip_id','simplified_trip_id']

    for dim_size in hex_str_dims:
        size = dim_size.strip()
        grid_col_name = f"hex_{size}_column"
        grid_row_name = f"hex_{size}_row"
        result.append(grid_col_name)
        result.append(grid_row_name)
    
    for dim_size in square_str_dims:
        size = dim_size.strip()
        grid_col_name = f"square_{size}_column"
        grid_row_name = f"square_{size}_row"
        result.append(grid_col_name)
        result.append(grid_row_name)
    
    return result

def insert_into_star(df: gpd.GeoDataFrame, logger):
    # Establish db connection
    conn = psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB, port="5432")
    conn_wrapper = pygrametl.ConnectionWrapper(connection=conn)

    logger.info("Converting back to 4326")
    trip_id = df['trip_id'].min()

    df = insert_columns_for_grids(df)

    df = df.astype(object).where(pd.notnull(df),None)

    fact_table_key_refs = get_fact_table_key_refs()

    ais_source = PandasSource(df)

    date_dim = CachedDimension(
        name='date_dim',
        key='date_id',
        attributes=['date','year','month','day'],
        lookupatts=['date'],
        cacheoninsert=True,
        prefill=True
    )

    nav_dim = CachedDimension(
        name='nav_dim',
        key='nav_id',
        attributes=['navigational_status'],
        lookupatts=['navigational_status'],
        cacheoninsert=True,
        prefill=True
    )

    ship_dim = CachedDimension(
        name='ship_dim',
        key='ship_id',
        attributes=['mmsi','type_of_mobile','imo','name','callsign','type_of_position_fixing_device','width','length'],
        lookupatts=['mmsi'],
        cacheoninsert=True,
        prefill=True
    )

    ship_type_dim = CachedDimension(
        name='ship_type_dim',
        key='ship_type_id',
        attributes=['ship_type'],
        lookupatts=['ship_type'],
        cacheoninsert=True,
        prefill=True
    )

    time_dim = CachedDimension(
        name='time_dim',
        key='time_id',
        attributes=['time','hour','quarter_hour','five_minutes'],
        lookupatts=['time'],
        cacheoninsert=True,
        prefill=True
    )

    trip_dim = CachedDimension (
        name='trip_dim',
        key='trip_id',
        attributes=['line_string']
    )

    fact_table = BatchFactTable(
        name='data_fact',
        keyrefs=fact_table_key_refs,
        measures=['location','rot','sog','cog','heading','draught','destination'],
        batchsize=500000,
        targetconnection=conn_wrapper
    )

    logger.info("Inserting rows into star schema")
    time_begin = datetime.datetime.now()
    logger.info("Time begin: " + time_begin.strftime("%d-%m-%Y, %H:%M:%S"))

    for row in ais_source:
        if row['date_id'] != date_dim.getbykey(row)['date_id']:
            date_dim.insert(row)

        if row['time_id'] != time_dim.getbykey(row)['time_id']:
            time_dim.insert(row)

        row['nav_id'] = nav_dim.ensure(row)
        row['ship_id'] = ship_dim.ensure(row)
        row['ship_type_id'] = ship_type_dim.ensure(row)

        if row['trip_id'] != trip_dim.getbykey(row)['trip_id']:
            trip_dim.insert(row)

        fact_table.insert(row)

    conn_wrapper.commit()
    conn_wrapper.close()
    conn.close()
    
    time_end = datetime.datetime.now()
    time_delta = time_end - time_begin
    logger.info("Done inserting into star schema")
    logger.info("Time end (star schema): " + time_end.strftime("%d%m%Y, %H:%M%S"))
    logger.info(f"Took approx (star schema): {time_delta.total_seconds() / 60} minutes")

    logger.info("Generating line strings, simplified line strings, and updating data_fact with the corresponding keys...")
    create_line_strings(trip_id=trip_id, threshold=1000)

    logger.info("Done with line strings, adding (col,row) on data_fact for the hexagons dimensions...")
    hex_str_dims = get_resolutions_from_config_file(hexagons=True).split(",")
    square_str_dims = get_resolutions_from_config_file(hexagons=False).split(",")
    create_hex_ids(square_resolutions=square_str_dims, hex_resolutions=hex_str_dims, simplified_trip_id=trip_id)

    logger.info("Adding hex (col, row) finished!")
    logger.info("Vacuuming and analyzing the tables...")
    vacuum_and_analyze_tables()

    logger.info("Finished vacuuming and analyzing!")
    logger.info("Finished!")