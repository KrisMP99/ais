from venv import create
import numpy as np
from dotenv import load_dotenv
import psycopg2
import os
import pygrametl
from pygrametl.datasources import PandasSource
from pygrametl.tables import CachedDimension, BatchFactTable, FactTable
from sqlalchemy import create_engine
import datetime
import geopandas as gpd
from shapely import wkb
import pandas as pd
from psycopg2.errors import NumericValueOutOfRange

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
HOST_DB = os.getenv('HOST_DB')
DB_NAME = os.getenv('DB_NAME')
COLUMNS = ['timestamp', 'type_of_mobile', 'mmsi', 'location','latitude','longitude', 'navigational_status', 'rot', 'sog', 'cog', 'heading', 'imo', 'callsign', 'name', 'ship_type', 'width', 'length', 'type_of_position_fixing_device', 'draught', 'destination', 'trip_id', 'simplified_trip_id']
cleansed_table_sql = "CREATE TABLE IF NOT EXISTS cleansed ( \
                      timestamp TIMESTAMP WITHOUT TIME ZONE,\
                      type_of_mobile VARCHAR,\
                      mmsi integer,\
                      latitude real,\
                      longitude real,\
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

def insert_cleansed_data(df,logger):
    db_string = f"postgresql://{USER}:{PASS}@{HOST_DB}/{DB_NAME}"
    logger.info("Inserting data into cleansed table...")
    engine = create_engine(db_string)
    with engine.connect() as conn:
        conn.execute(cleansed_table_sql)
        df.to_sql('cleansed', conn, if_exists='append', index=False, chunksize=500000)
    logger.info("Done inserting!")


def convert_timestamp_to_date(row):
    timestamp = str(row['timestamp'])
    return (timestamp.split(' ')[0])

def convert_timestamp_to_time_and_date(row):
    timestamp = str(row['timestamp'])
    
    time_split = timestamp.split(' ')
    row['date'] = time_split[0]

    seconds_elapsed = np.ceil((row['timestamp'] - row['timestamp'].replace(hour=0,minute=0,second=0,microsecond=0)).total_seconds())
    row['time'] = datetime.timedelta(seconds=seconds_elapsed)

    row['date_id'] = int(time_split[0].replace('-',''))
    row['time_id'] = int(time_split[1].replace(':',''))

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
    print(simplified_trip_df.columns)
    logger.info("Inserting simplified trips into 'simplified_trip_dim'")
    simplified_trip_df.to_postgis("simplified_trip_dim",con=engine, if_exists='append')
    logger.info("Finished inserting simplified trips into 'simplified_trip_dim'")


def convert_to_hex(row):
    row['location'] = wkb.dumps(row['location'], hex=True, srid=4326)

def insert_into_star(df: gpd.GeoDataFrame, logger):
    # Establish db connection
    conn = psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB, port="5432")
    cursor = conn.cursor()
    conn_wrapper = pygrametl.ConnectionWrapper(connection=conn)
    logger.info("Converting back to 4326")

    df = df.to_crs(epsg="4326")
    df = df.rename(columns={'geometry':'location'})
    df = df.drop(['point'],axis=1, errors='ignore')
    df = df.astype(object).where(pd.notnull(df),None)
    df['line_string'] = None

    # print("In data_insertion")
    # print(type(df))
    # print(df.head())
    # print(df.columns)

    ais_source = PandasSource(df)

    date_dim = CachedDimension(
        name='date_dim',
        key='date_id',
        attributes=['date'],
        lookupatts=['date'],
        cacheoninsert=True,
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
        attributes=['time'],
        lookupatts=['time'],
        cacheoninsert=True
    )

    trip_dim = CachedDimension (
        name='trip_dim',
        key='trip_id',
        attributes=['line_string'],
        lookupatts=['line_string']
    )

    # simplified_trip_dim = CachedDimension (
    #     name='simplified_trip_dim',
    #     key='simplified_trip_id',
    #     attributes=['line_string'],
    #     lookupatts=['line_string']
    # )

    fact_table = FactTable(
        name='data_fact',
        keyrefs=['date_id','time_id','ship_type_id','ship_id','nav_id','trip_id','simplified_trip_id'],
        measures=['location','rot','sog','cog','heading','draught','destination'],
        targetconnection=conn_wrapper
    )

    logger.info("Inserting rows into star schema")
    time_begin = datetime.datetime.now()
    print("Time begin: " + time_begin.strftime("%d-%m-%Y, %H:%M:%S"))
    for row in ais_source:
        convert_timestamp_to_time_and_date(row)
        convert_to_hex(row)

        if row['date_id'] != date_dim.getbykey(row)['date_id']:
            date_dim.insert(row)

        if row['time_id'] != time_dim.getbykey(row)['time_id']:
            time_dim.insert(row)

        row['nav_id'] = nav_dim.ensure(row)
        row['ship_id'] = ship_dim.ensure(row)
        row['ship_type_id'] = ship_type_dim.ensure(row)

        if row['trip_id'] != trip_dim.getbykey(row)['trip_id']:
            trip_dim.insert(row)

        # if row['simplified_trip_id'] is not None:
        #     if row['simplified_trip_id'] != simplified_trip_dim.getbykey(row)['simplified_trip_id']:
        #         simplified_trip_dim.insert(row)

        fact_table.insert(row)


    time_end = datetime.datetime.now()
    time_delta = time_end - time_begin
    print("Time end: " + time_end.strftime("%d%m%Y, %H:%M%S"))
    print(f"Took approx: {time_delta.total_seconds() / 60} minutes")
    logger.info("Done inserting into star schema")
    logger.info("Generating line strings...")

    trip_id = df['trip_id'].min()

    # truncate table data_fact, date_dim, nav_dim, ship_dim, ship_type_dim, simplified_trip_dim, time_dim, trip_dim RESTART IDENTITY CASCADE
    sql_line_string_query = "WITH trip_list AS ( " \
                                "SELECT trip_id, ST_MakeLine(array_agg(location ORDER BY time_id ASC)) as line " \
                                "FROM data_fact " \
                                f"WHERE trip_id >= {trip_id} " \
                                "GROUP BY trip_id) " \
                            "UPDATE trip_dim " \
                                "SET line_string = ( " \
	                                "SELECT line " \
	                                "FROM trip_list " \
	                            "WHERE trip_list.trip_id = trip_dim.trip_id)"

    # sql_simplified_line_query = "WITH trip_list AS ( " \
    #                             "SELECT simplified_trip_id, ST_MakeLine(array_agg(location ORDER BY time_id ASC)) as line " \
    #                             "FROM data_fact " \
    #                             f"WHERE simplified_trip_id > {simplified_trip_id} " \
    #                             "GROUP BY simplified_trip_id) " \
    #                         "UPDATE simplified_trip_dim " \
    #                             "SET line_string = ( " \
	#                                 "SELECT line " \
	#                                 "FROM trip_list " \
	#                             "WHERE trip_list.simplified_trip_id = simplified_trip_dim.simplified_trip_id)"

    cursor.execute(sql_line_string_query)
    # cursor.execute(sql_simplified_line_query)

    logger.info("Generated and updated all line strings. Commiting data...")

    # cursor.execute("DROP TABLE cleansed, raw_data")

    conn_wrapper.commit()
    conn_wrapper.close()
    conn.close()
    
    logger.info("Finished!")


