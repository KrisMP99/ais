from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from app.dependencies import get_token_header
from app.models.coordinate import Coordinate
from app.db.database import engine, Session
from geojson import Point
import asyncio
import pandas as pd

session = Session()
router = APIRouter(
    prefix="/trips",
    tags=["trips"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

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