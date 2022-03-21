from tarfile import POSIX_MAGIC
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
import data_cleansing as dc

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
HOST_DB = os.getenv('HOST_DB')
DB_NAME = os.getenv('DB_NAME')

pgconn = psycopg2.connect(database="aisdb", user=USER, password=PASS, host="localhost", port="5432")
pgconn_wrapper = pygrametl.ConnectionWrapper(connection=pgconn)



def convert_timestamp_to_time_and_date(timestamp):
    print(timestamp)

for timestamp in zip(df.timestamp):
    convert_timestamp_to_time_and_date(timestamp[0])



