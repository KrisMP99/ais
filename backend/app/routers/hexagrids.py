from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_token_header, get_logger
from app.db.database import engine, Session
from app.models.coordinate import Coordinate
from shapely.geometry.point import Point
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
    geomPoint = Point(p1.long, p1.lat)
    query = '''
                SELECT
                    ST_AsGeoJSON(
                        ST_FlipCoordinates(h.geom)
                    )::json AS st_asgeojson
                FROM
                    hexagrid AS h
                WHERE
                    ST_Intersects(
                        h.geom, ST_GeomFromWKB(%(geom)s::geometry, 3857)
                    );
            '''

    result = pd.read_sql_query(query, engine, params={'geom': geomPoint.wkb_hex})

    if len(result) == 0:
        logger.error('Could not find the given coordinates')
        raise HTTPException(status_code=404, detail='Could not find the given coordinates')
    polygon = result['st_asgeojson'][0]['coordinates'][0]

    return polygon

@router.post('/hexagon-centroid')
async def get_hexagon_centroid(p1: Coordinate):
    geomPoint = Point(p1.long, p1.lat)
    query = '''
                SELECT 
                    ST_AsGeoJSON(
                        ST_Centroid(
                            ST_FlipCoordinates(h.geom)
                        )
                    )::json AS st_asgeojson
                FROM 
                    hexagrid as h
                WHERE 
                    ST_Intersects(
                        h.geom, ST_GeomFromWKB(%(geom)s::geometry, 3857)
                    );
            '''

   
    df = await pd.read_sql_query(query, engine,params={'geom': geomPoint.wkb_hex})

    if len(df) == 0:
        logger.error('Could not find the given coordinates')
        raise HTTPException(status_code=404, detail='Could not find the given coordinates')
        
    polygon = df['st_asgeojson'][0]['coordinates']
    
    return polygon

# @router.get("/hexagrid")
# async def get_hexa_grid():
#     query = 'SELECT ST_AsGeoJSON(geom)::json FROM hexagrid ORDER BY(geom);'
#     #query = "SELECT jsonb_build_object('type', 'FeatureCollection', 'features', json_agg(ST_AsGeoJSON(t.*)::json)) FROM hexagrid AS t(hid, geom);"
#     loop = asyncio.get_event_loop()
#     feature_collection = await loop.run_in_executor(None, pd.read_sql, query, engine)

#     return jsonable_encoder(feature_collection[1])