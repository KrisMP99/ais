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
import douglas_peucker as dp
from sqlalchemy import create_engine


load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
HOST_DB = os.getenv('HOST_DB')
DB_NAME = os.getenv('DB_NAME')

db_string = f"postgresql://{USER}:{PASS}@{HOST_DB}/{DB_NAME}"
engine = create_engine(db_string)
# pgconn = psycopg2.connect(database="aisdb", user=USER, password=PASS, host="localhost", port="5432")
# pgconn_wrapper = pygrametl.ConnectionWrapper(connection=pgconn)

def insert_cleansed_data(df):
    df.to_sql('cleansed', engine, if_exists='append', index=False)

def convert_timestamp_to_time_and_date(timestamp):
    print(timestamp)

df = dp.create_line_strings()
insert_cleansed_data(df)





