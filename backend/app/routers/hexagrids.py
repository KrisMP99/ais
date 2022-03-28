from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from app.dependencies import get_token_header
from app.db.database import engine, Session
from app.models.coordinate import Coordinate
from geojson import Polygon
import asyncio
import pandas as pd

session = Session()
router = APIRouter(
    prefix="/hexagrids",
    tags=["hexagrids"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.put('/index_hexagrid')
async def index_hexagrid():
    query = "SELECT ST_AsGeoJSON(h.geom)::json FROM hexagrid AS h"
    polygon_coordinates = []
    for chunk in pd.read_sql_query(query , engine, chunksize=50000):  
        for json in chunk['st_asgeojson']:
            json['PK'] = {'row': 1, 'column': 2}  
            polygon_coordinates.append(json['coordinates'][0])
    print(polygon_coordinates[0])
    print('Got all hexagons as json from database')
    print('Began sorting...')
    
    sorted_coordinates = sorted(polygon_coordinates)
    return jsonable_encoder(sorted_coordinates[1], sorted_coordinates[2], sorted_coordinates[3])

@router.get("/hexa_grid")
async def get_map_bounds():
    query = 'SELECT ST_AsGeoJSON(geom) FROM hexagrid ORDER BY(geom);'
    #query = "SELECT jsonb_build_object('type', 'FeatureCollection', 'features', json_agg(ST_AsGeoJSON(t.*)::json)) FROM hexagrid AS t(hid, geom);"
    loop = asyncio.get_event_loop()
    feature_collection = await loop.run_in_executor(None, pd.read_sql, query, engine)

    return jsonable_encoder(feature_collection[1])