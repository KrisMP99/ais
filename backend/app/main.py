import asyncio
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
    query = "SELECT ST_AsGeoJSON(geom) FROM hexagrid ORDER BY(geom);"
    # SELECT jsonb_build_object('type', 'FeatureCollection', 'features', json_agg(ST_AsGeoJSON(t.*)::json)) FROM hexagrid AS t(hid, geom);
    #feature_collection = pd.read_sql(query, engine)
    # df = pd.DataFrame(feature_collection)
    loop = asyncio.get_event_loop()
    feature_collection = await loop.run_in_executor(None, pd.read_sql, query, engine)
    #feature_collection_dict = feature_collection.iloc[0]['jsonb_build_object']
    
    return jsonable_encoder(feature_collection)