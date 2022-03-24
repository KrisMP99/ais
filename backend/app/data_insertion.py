from multiprocessing import connection
from venv import create
import numpy as np
from dotenv import load_dotenv
import psycopg2
import os
import pygrametl
from pygrametl.datasources import SQLSource
from pygrametl.tables import CachedDimension, FactTable
from sqlalchemy import create_engine

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
HOST_DB = os.getenv('HOST_DB')
DB_NAME = os.getenv('DB_NAME')

# conn = psycopg2.connect(database="aisdb", user=USER, password=PASS, host="localhost", port="5432")
# conn.autocommit = True
# cursor = conn.cursor()

def insert_cleansed_data(df):
    db_string = f"postgresql://{USER}:{PASS}@{HOST_DB}/{DB_NAME}"
    
    engine = create_engine(db_string)
    with engine.connect() as conn:
        df.to_sql('cleansed', conn, if_exists='append', index=False, chunksize=500000)

def convert_timestamp_to_date(row):
    timestamp = str(row['timestamp'])
    return (timestamp.split(' ')[0])


def convert_timestamp_to_time_and_date(row):
    timestamp = str(row['timestamp'])
    
    time_split = timestamp.split(' ')
    row['date'] = time_split[0]

    row['time'] = np.ceil((row['timestamp'] - row['timestamp'].replace(hour=0,minute=0,second=0,microsecond=0)).total_seconds()/60/10)
    
    row['date_id'] = int(time_split[0].replace('-',''))
    row['time_id'] = int(time_split[1].replace(':',''))

    #return date, time, date_id, time_id

def insert_into_star(df):
    print("Inserting DF to cleansed")
    insert_cleansed_data(df)

    # Update all rows with data for date- and time dimensions
    # df[["date","time","date_id","time_id"]] = df.apply(convert_timestamp_to_time_and_date, axis=1, result_type="expand")

    # Establish db connection
    conn = psycopg2.connect(database="aisdb", user=USER, password=PASS, host="localhost", port="5432")
    cursor = conn.cursor()
    conn_wrapper = pygrametl.ConnectionWrapper(connection=conn)

    print("Getting cleansed data from db")
    sql_query = "SELECT *, ST_SetSRID(ST_MakePoint(latitude,longitude),3857) AS location FROM cleansed"
    ais_source = SQLSource(connection=conn, query=sql_query)

    date_dim = CachedDimension(
        name='date_dim',
        key='date_id',
        attributes=['date']
    )

    nav_dim = CachedDimension(
        name='nav_dim',
        key='nav_id',
        attributes=['navigational_status']
    )

    ship_dim = CachedDimension(
        name='ship_dim',
        key='ship_id',
        attributes=['mmsi','type_of_mobile','imo','name','callsign','type_of_position_fixing_device','width','length']
    )

    ship_type_dim = CachedDimension(
        name='ship_type_dim',
        key='ship_type_id',
        attributes=['ship_type']
    )

    time_dim = CachedDimension(
        name='time_dim',
        key='time_id',
        attributes=['time']
    )

    trip_dim = CachedDimension (
        name='trip_dim',
        key='trip_id',
        attributes=['line_string']
    )

    fact_table = FactTable(
        name='data_fact',
        keyrefs=['date_id','time_id','ship_type_id','ship_id','nav_id','trip_id'],
        measures=['location','rot','sog','cog','heading','draught','destination'],
        targetconnection=conn_wrapper
    )

    print("Inserting rows...")
    index = 0
    for row in ais_source:
        convert_timestamp_to_time_and_date(row)
        row['line_string'] = None
        row['date_id'] = date_dim.ensure(row)
        row['time_id'] = time_dim.ensure(row)
        row['nav_id'] = nav_dim.ensure(row)
        row['ship_id'] = ship_dim.ensure(row)
        row['ship_type_id'] = ship_type_dim.ensure(row)
        row['trip_id'] = trip_dim.ensure(row)

        if(index % 100000 == 0):
            print(row)
        
        index += 1

        fact_table.insert(row)
    print("Done inserting!")

    # Truncate cleansed table:
    cursor.execute("TRUNCATE TABLE cleansed")

    conn_wrapper.commit()
    conn_wrapper.close()
    conn.close()
    # print(df.head(10))
    # quit()


