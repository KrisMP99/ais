from email.policy import HTTP
from sre_constants import SUCCESS
from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from app.dependencies import get_token_header
from app.models.coordinate import Coordinate
from app.db.database import engine, Session
from geojson import Feature, Point, FeatureCollection
import asyncio
import pandas as pd

session = Session()
router = APIRouter(
    prefix="/trips",
    tags=["trips"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.get('/')
async def root():
    return {'message': ':)'}

@router.post('/trip')
async def get_trip(p1: Coordinate, p2: Coordinate): 
    gp1 = Point((p1.long, p1.lat))
    gp2 = Point((p2.long, p2.lat))
    query = f"WITH gp1 AS (\
        SELECT ST_AsText(ST_GeomFromGeoJSON('{gp1}')) As geom),\
        gp2 AS (SELECT ST_AsText(ST_GeomFromGeoJSON('{gp2}')) As geom)\
        SELECT ST_AsGeoJSON(h.geom)\
        FROM hexagrid as h, gp1, gp2\
        WHERE ST_Intersects(h.geom, ST_SetSRID(gp1.geom, 3857))\
        OR ST_Intersects(h.geom, ST_SetSRID(gp2.geom, 3857));"

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, pd.read_sql, query, engine)

    return jsonable_encoder(result)

@router.get("/hexa_grid")
async def get_map_bounds():
    query = 'SELECT ST_AsGeoJSON(geom) FROM hexagrid ORDER BY(geom);'
    # SELECT jsonb_build_object('type', 'FeatureCollection', 'features', json_agg(ST_AsGeoJSON(t.*)::json)) FROM hexagrid AS t(hid, geom);
    #feature_collection = pd.read_sql(query, engine)
    # df = pd.DataFrame(feature_collection)
    loop = asyncio.get_event_loop()
    feature_collection = await loop.run_in_executor(None, pd.read_sql, query, engine)
    #feature_collection_dict = feature_collection.iloc[0]['jsonb_build_object']

    return jsonable_encoder(feature_collection)