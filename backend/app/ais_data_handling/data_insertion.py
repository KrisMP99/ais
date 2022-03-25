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
import datetime

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

# Remember to refactor/rewrite!!
def convert_timestamp_to_time_and_date(row):
    timestamp = str(row['timestamp'])
    
    time_split = timestamp.split(' ')
    row['date'] = time_split[0]

    # row['time'] = np.ceil((row['timestamp'] - row['timestamp'].replace(hour=0,minute=0,second=0,microsecond=0)).total_seconds()/60/10)
    seconds_elapsed = np.ceil((row['timestamp'] - row['timestamp'].replace(hour=0,minute=0,second=0,microsecond=0)).total_seconds())
    row['time'] = datetime.timedelta(seconds=seconds_elapsed)

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

        if row['date_id'] != date_dim.getbykey(row)['date_id']:
            date_dim.insert(row)

        if row['time_id'] != time_dim.getbykey(row)['time_id']:
            time_dim.insert(row)

        row['nav_id'] = nav_dim.ensure(row)
        row['ship_id'] = ship_dim.ensure(row)
        row['ship_type_id'] = ship_type_dim.ensure(row)

        if row['trip_id'] != trip_dim.getbykey(row)['trip_id']:
            trip_dim.insert(row)

        if(index % 1000000 == 0):
            print(f"Inserted {index} rows into star schema...")
        
        index += 1

        fact_table.insert(row)

    print("Done inserting!")
    print("Create line strings...")
    # Get the line string to start from
    cursor.execute("SELECT MIN(trip_id) FROM cleansed")
    result = cursor.fetchone()
    trip_id = result[0]

    sql_line_string_query = "WITH trip_list AS ( " \
                            "SELECT trip_id, ST_MakeLine(array_agg(location ORDER BY time_id ASC)) as line " \
                            "FROM data_fact " \
                            f"WHERE trip_id >= {trip_id}" \
                            "GROUP BY trip_id)" \
                            "UPDATE trip_dim " \
                            "SET line_string = ( " \
	                        "SELECT line " \
	                        "FROM trip_list " \
	                        "WHERE trip_list.trip_id = trip_dim.trip_id)"


    # Truncate cleansed table:
    cursor.execute(sql_line_string_query)
    cursor.execute("TRUNCATE TABLE cleansed")

    conn_wrapper.commit()
    conn_wrapper.close()
    conn.close()
    # print(df.head(10))
    # quit()


