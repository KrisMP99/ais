from venv import create
import pandas as pd, numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString
from dotenv import load_dotenv
import data_cleansing as dc
import psycopg2
import os
import pygrametl
from pygrametl.datasources import SQLSource
from pygrametl.tables import Dimension, FactTable
from sqlalchemy import create_engine
import pandas.io.sql as psql


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
    df.to_sql('cleansed', engine, if_exists='append', index=False)

def convert_timestamp_to_date(row):
    timestamp = str(row['timestamp'])
    return (timestamp.split(' ')[0])


def convert_timestamp_to_time_and_date(row):
    timestamp = str(row['timestamp'])
    
    time_split = timestamp.split(' ')
    date = time_split[0]

    time = np.ceil((row['timestamp'] - row['timestamp'].replace(hour=0,minute=0,second=0,microsecond=0)).total_seconds()/60/10)
    
    date_id = int(time_split[0].replace('-',''))
    time_id = int(time_split[1].replace(':',''))

    return date, time, date_id, time_id

def insert_into_star(df):
    # Add the columns needed for date- and time dimensions
    # df["date"] = '' #df.apply(lambda row : convert_timestamp_to_date(row), axis=1)
    # df["time"] = ''
    # df["date_id"] = ''
    # df["time_id"] = ''

    # Update all rows with data for date- and time dimensions
    df[["date","time","date_id","time_id"]] = df.apply(convert_timestamp_to_time_and_date, axis=1, result_type="expand")

    print(df.head(10))
    quit()


