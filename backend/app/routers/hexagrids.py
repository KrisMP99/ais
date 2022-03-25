from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from app.dependencies import get_token_header
from app.db.database import engine, Session
from app.models.polygon import Polygon
from app.models.coordinate import Coordinate
#from geojson import Polygon
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
    polygon_collection = []
    for chunk in pd.read_sql_query(query , engine, chunksize=50000):  
        for json in chunk['st_asgeojson']:
            json['PK'] = {'row': 1, 'column': 2}  
            polygon = Polygon(
                p1=Coordinate(long=json['coordinates'][0][0][0], lat=json['coordinates'][0][0][1]),
                p2=Coordinate(long=json['coordinates'][0][1][0], lat=json['coordinates'][0][1][1]),
                p3=Coordinate(long=json['coordinates'][0][2][0], lat=json['coordinates'][0][2][1]),
                p4=Coordinate(long=json['coordinates'][0][3][0], lat=json['coordinates'][0][3][1]),
                p5=Coordinate(long=json['coordinates'][0][4][0], lat=json['coordinates'][0][4][1]),
                p6=Coordinate(long=json['coordinates'][0][5][0], lat=json['coordinates'][0][5][1]),
                p7=Coordinate(long=json['coordinates'][0][6][0], lat=json['coordinates'][0][6][1])
            )

            polygon_collection.append(polygon) 
    
    print('Got all hexagons as json from database')
    print('Began sorting...')

    #featureCollection.sort(key=lambda x: (['coordinates'][0][0], ['coordinates'][0][1]))
    #print(len(featureCollection))
    return jsonable_encoder(polygon_collection[0])

@router.get("/hexa_grid")
async def get_map_bounds():
    query = 'SELECT ST_AsGeoJSON(geom) FROM hexagrid ORDER BY(geom);'
    #query = "SELECT jsonb_build_object('type', 'FeatureCollection', 'features', json_agg(ST_AsGeoJSON(t.*)::json)) FROM hexagrid AS t(hid, geom);"
    loop = asyncio.get_event_loop()
    feature_collection = await loop.run_in_executor(None, pd.read_sql, query, engine)

    return jsonable_encoder(feature_collection[1])