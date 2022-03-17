import asyncio
import os
from fastapi import FastAPI, Response, Security, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.security.api_key import APIKeyQuery, APIKeyCookie, APIKeyHeader, APIKey
from starlette.status import HTTP_403_FORBIDDEN
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd

from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware


load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
TESTSERVER = os.getenv('TEST_SERVER')
PRODSERVER = os.getenv('PRODUCTION_SERVER')
API_KEY = os.getenv('API_KEY')
API_KEY_NAME = os.getenv('access_token')

api_key_query = APIKeyQuery(name=API_KEY_NAME, auto_error=False)
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)
api_key_cookie = APIKeyCookie(name=API_KEY_NAME, auto_error=False)

SQLALCHEMY_DATABASE_URL = f'postgresql://{USER}:{PASS}@db/aisdb'
engine = create_engine( SQLALCHEMY_DATABASE_URL, convert_unicode=True )

Session = sessionmaker(bind=engine)
session = Session() 

app = FastAPI()
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    f"http://{TESTSERVER}",
    f"http://{PRODSERVER}"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_api_key(
    api_key_query: str = Security(api_key_query),
    api_key_header: str = Security(api_key_header),
    api_key_cookie: str = Security(api_key_cookie),
):
    if api_key_query == API_KEY:
        return api_key_query
    elif api_key_header == API_KEY:
        return api_key_header
    elif api_key_cookie == API_KEY:
        return api_key_cookie
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
            )

@app.get("/")
async def root(response: Response, api_key: APIKey = Depends(get_api_key)):
    response.set_cookie(
        API_KEY_NAME,
        value=api_key,
        httponly=True,
        max_age=1800,
        expires=1800
    )
    return {"message": "Hello World"}
    

@app.get("/map_bounds")
async def get_mapBounds(response: Response, api_key: APIKey = Depends(get_api_key)):
    query = "SELECT ST_AsGeoJSON(geom) FROM hexagrid ORDER BY(geom);"
    # SELECT jsonb_build_object('type', 'FeatureCollection', 'features', json_agg(ST_AsGeoJSON(t.*)::json)) FROM hexagrid AS t(hid, geom);
    #feature_collection = pd.read_sql(query, engine)
    # df = pd.DataFrame(feature_collection)
    loop = asyncio.get_event_loop()
    feature_collection = await loop.run_in_executor(None, pd.read_sql, query, engine)
    #feature_collection_dict = feature_collection.iloc[0]['jsonb_build_object']
    
    response.set_cookie(
        API_KEY_NAME,
        value=api_key,
        httponly=True,
        max_age=1800,
        expires=1800
    )

    return jsonable_encoder(feature_collection)