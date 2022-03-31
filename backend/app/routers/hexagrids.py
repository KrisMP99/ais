from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_token_header, get_logger
from app.db.database import engine, Session
from app.models.coordinate import Coordinate
from geojson import Point
import asyncio
import pandas as pd

session = Session()
logger = get_logger()
router = APIRouter(
    prefix="/hexagrids",
    tags=["hexagrids"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.post('/hexagon')
async def get_hexagon(p1: Coordinate):
    gp1 = Point((p1.long, p1.lat))
    query = f"WITH gp1 AS (\
    SELECT ST_AsText(ST_GeomFromGeoJSON('{gp1}')) As geom)\
    SELECT ST_AsGeoJSON(ST_FlipCoordinates(h.geom))::json AS st_asgeojson\
    FROM hexagrid as h, gp1\
    WHERE ST_Intersects(h.geom, ST_SetSRID(gp1.geom, 3857));"

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, pd.read_sql_query, query, engine)

    if len(result) == 0:
        logger.error('Could not find the given coordinates')
        raise HTTPException('Could not find the given coordinates')
    polygon = result['st_asgeojson'][0]['coordinates'][0]

    return polygon

# @router.get("/hexagrid")
# async def get_hexa_grid():
#     query = 'SELECT ST_AsGeoJSON(geom)::json FROM hexagrid ORDER BY(geom);'
#     #query = "SELECT jsonb_build_object('type', 'FeatureCollection', 'features', json_agg(ST_AsGeoJSON(t.*)::json)) FROM hexagrid AS t(hid, geom);"
#     loop = asyncio.get_event_loop()
#     feature_collection = await loop.run_in_executor(None, pd.read_sql, query, engine)

#     return jsonable_encoder(feature_collection[1])