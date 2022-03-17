import imp
import os
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import pandas.io.sql as psql
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')

SQLALCHEMY_DATABASE_URL = f"postgresql://{USER}:{PASS}@db/aisdb"
engine = create_engine( SQLALCHEMY_DATABASE_URL, convert_unicode=True )

Session = sessionmaker(bind=engine)
session = Session() 

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/map_bounds")
async def get_mapBounds():
    query = "WITH geometry_hexagons \
        AS (SELECT hexes.geom  \
            FROM ST_SquareGrid\
                (0.5, ST_SetSRID(ST_EstimatedExtent('map_bounds','geom'), 4326))\
                AS hexes INNER JOIN map_bounds AS mb \
                ON ST_Intersects(mb.geom, ST_Transform(hexes.geom, 4326)) \
            GROUP BY hexes.geom)\
        SELECT ST_AsGeoJson(gh.geom::Geography) \
        FROM geometry_hexagons AS gh;"
    sql = psql.read_sql_query(sql=query, con=engine)
    df = pd.DataFrame(sql)
    return df