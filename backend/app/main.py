import imp
import os
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import pandas.io.sql as psql

USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')

SQLALCHEMY_DATABASE_URL = "postgresql://{USER}:{PASS}@db/aisdb"
engine = create_engine( SQLALCHEMY_DATABASE_URL, convert_unicode=True )

Session = sessionmaker(bind=engine)
session = Session() 

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/map_bounds")
async def get_mapBounds(GeoJson):
    query = "SELECT hexes.geom \
                FROM ST_HexagonGrid(\
                    500,\
                    ST_SetSRID(\
                        ST_EstimatedExtent('map_bounds','geom'), 3857\
                    )\
                ) AS hexes INNER JOIN\
                    map_bounds AS mb ON ST_Intersects(mb.geom, hexes.geom) \
            GROUP BY hexes.geom;"
    sql = psql.read_sql_query(sql=query, con=engine)
    df = pd.DataFrame(sql)
    print(df)