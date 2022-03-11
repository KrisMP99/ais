import imp
import os
import json
from geojson import Feature, FeatureCollection, Polygon
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
import pandas.io.sql as psql
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')

SQLALCHEMY_DATABASE_URL = f"postgresql://{USER}:{PASS}@db/aisdb"
engine = create_engine( SQLALCHEMY_DATABASE_URL, convert_unicode=True )

Session = sessionmaker(bind=engine)
session = Session() 

app = FastAPI()
origins = [
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/map_bounds")
async def get_mapBounds():
    # query = "WITH geometry_hexagons \
    #     AS (SELECT mb.gid, hexes.geom  \
    #         FROM ST_HexagonGrid\
    #             (0.01, ST_SetSRID(ST_EstimatedExtent('map_bounds','geom'), 4326))\
    #             AS hexes INNER JOIN map_bounds AS mb \
    #             ON ST_Intersects(mb.geom, ST_Transform(hexes.geom, 4326)) \
    #         GROUP BY (hexes.geom, mb.gid))\
    #     INSERT INTO geo_json_collection SELECT json_build_object(\
    #         'type', 'FeatureCollection',\
    #         'features', json_agg(ST_AsGeoJSON(t.*)::json))\
    #     FROM geometry_hexagons AS t(id, geom);"

    query = "SELECT * FROM geo_json_collection"

    feature_collection = pd.read_sql(query, engine)
    #feature_collection_dict = feature_collection.iloc[0]
    df = pd.DataFrame(feature_collection, columns=['geojson'])

    
    return jsonable_encoder(df['geojson'])