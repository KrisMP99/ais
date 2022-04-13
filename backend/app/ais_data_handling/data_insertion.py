from venv import create
import numpy as np
from dotenv import load_dotenv
import psycopg2
import os
import pygrametl
from pygrametl.datasources import SQLSource, PandasSource
from pygrametl.tables import CachedDimension, BatchFactTable, FactTable
from sqlalchemy import create_engine
import datetime
import geopandas as gpd
from shapely import wkb
import pandas as pd

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


def convert_timestamp_to_time_and_date(row):
    timestamp = str(row['timestamp'])
    
    time_split = timestamp.split(' ')
    row['date'] = time_split[0]

    date_split = time_split[0].split('-')
    row['year'] = date_split[0]
    row['month'] = date_split[1]
    row['day'] = date_split[2]

    seconds_elapsed = np.ceil((row['timestamp'] - row['timestamp'].replace(hour=0,minute=0,second=0,microsecond=0)).total_seconds())

    hours = round((seconds_elapsed / 60) / 60)
    quarter_hours = round((seconds_elapsed / 60) / 15)
    five_minutes = round((seconds_elapsed / 60) / 5)
    row['hour'] = hours
    row['quarter_hour'] = quarter_hours
    row['five_minutes'] = five_minutes

    hours_time = int((seconds_elapsed / 60) / 60)
    minutes = int((seconds_elapsed % 3600) / 60)
    seconds = int((seconds_elapsed % 3600) % 60)

    row['time'] = datetime.time(hours_time, minutes, seconds)

    row['date_id'] = int(time_split[0].replace('-',''))
    row['time_id'] = int(time_split[1].replace(':',''))

    return row


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

def insert_into_star(trip_id, simplified_trip_id, df: gpd.GeoDataFrame, logger):
    # Establish db connection
    conn = psycopg2.connect(database="aisdb", user=USER, password=PASS, host=HOST_DB, port="5432")
    cursor = conn.cursor()
    conn_wrapper = pygrametl.ConnectionWrapper(connection=conn)
    logger.info("Converting back to 4326")

    df[['hex_500_column', 'hex_500_row', 'hex_10000_column', 'hex_10000_row']] = None

    df = df.astype(object).where(pd.notnull(df),None)

    ais_source = PandasSource(df)

    date_dim = CachedDimension(
        name='date_dim',
        key='date_id',
        attributes=['date','year','month','day'],
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
        attributes=['time','hour','quarter_hour','five_minutes'],
        lookupatts=['time'],
        cacheoninsert=True
    )

    trip_dim = CachedDimension (
        name='trip_dim',
        key='trip_id',
        attributes=['line_string'],
        lookupatts=['line_string']
    )

    fact_table = BatchFactTable(
        name='data_fact',
        keyrefs=['date_id','time_id','ship_type_id','ship_id','nav_id','trip_id','simplified_trip_id','hex_500_row', 'hex_500_column', 'hex_10000_column', 'hex_10000_row'],
        measures=['location','rot','sog','cog','heading','draught','destination'],
        batchsize=500000,
        targetconnection=conn_wrapper
    )

    logger.info("Inserting rows into star schema")
    time_begin = datetime.datetime.now()
    print("Time begin: " + time_begin.strftime("%d-%m-%Y, %H:%M:%S"))


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


    time_end = datetime.datetime.now()
    time_delta = time_end - time_begin
    print("Time end: " + time_end.strftime("%d%m%Y, %H:%M%S"))
    print(f"Took approx: {time_delta.total_seconds() / 60} minutes")
    logger.info("Done inserting into star schema")
    logger.info("Generating line strings...")

    # truncate table data_fact, date_dim, nav_dim, ship_dim, ship_type_dim, simplified_trip_dim, time_dim, trip_dim RESTART IDENTITY CASCADE
    sql_line_string_query = f'''WITH trip_list AS ( 
                                SELECT trip_id, ST_MakeLine(array_agg(location ORDER BY time_id ASC)) as line 
                                FROM data_fact 
                                WHERE trip_id >= {trip_id} 
                                GROUP BY trip_id) 
                            UPDATE trip_dim 
                                SET line_string = ( 
	                                SELECT line 
	                                FROM trip_list 
	                            WHERE trip_list.trip_id = trip_dim.trip_id)'''

    conn_wrapper.commit()
    cursor.execute(sql_line_string_query)
    conn.commit()

    logger.info("Done with line strings, adding (col,row) on data_fact for hex_10000_dim...")
    # Hexagons
    sql_hexagon_query = f'''
                            WITH hexes as (
                                SELECT hex_10000_dim.hex_10000_row as hex10row, hex_10000_dim.hex_10000_column as hex10col, data_fact.simplified_trip_id as data_id
                                FROM hex_10000_dim, data_fact
                                WHERE ST_Within(data_fact.location, hex_10000_dim.hexagon) AND (data_fact.simplified_trip_id >= {simplified_trip_id})
                            )

                            UPDATE data_fact
                            SET hex_10000_row = (
                                SELECT hexes.hex10row
                                FROM hexes
                                WHERE hexes.data_id = data_fact.simplified_trip_id
                            ),
                            hex_10000_column = (
                                SELECT hexes.hex10col
                                FROM hexes
                                WHERE hexes.data_id = data_fact.simplified_trip_id
                            )
                        '''
    cursor.execute(sql_hexagon_query)
    conn.commit()
    logger.info("Adding hex ids finished!")
    logger.info("Commiting data...")

    conn_wrapper.close()
    conn.close()
    
    logger.info("Finished!")


