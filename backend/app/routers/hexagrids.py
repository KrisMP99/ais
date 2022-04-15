from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_token_header, get_logger
from app.db.database import engine, Session
from app.models.coordinate import Coordinate
from shapely.geometry.point import Point
from shapely.geometry.polygon import Polygon
from app.models.hexagon import Hexagon
import shapely.wkb as wkb
import pandas as pd
import geopandas as gpd
import asyncio

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
    gp1 = Point(p1.long, p1.lat)
    query = '''
                SELECT
                    h.hex_10000_row, 
                    h.hex_10000_column, 
                    ST_FlipCoordinates(h.hexagon) AS hexagon
                FROM
                    hex_10000_dim AS h
                WHERE
                    ST_Within(
                        ST_GeomFromWKB(%(hexagon)s::geometry, 4326),
                        h.hexagon
                    );
            '''

    df = gpd.read_postgis(query, engine, params={'hexagon': gp1.wkb_hex}, geom_col='hexagon')

    if len(df) == 0:
        logger.error('Could not find the given coordinates')
        raise HTTPException(status_code=404, detail='Could not find the given coordinates')


    hex = Hexagon(
                row=df.hex_10000_row.iloc[0], 
                column=df.hex_10000_column.iloc[0], 
                hexagon=df.hexagon.iloc[0])
    return list(hex.hexagon.exterior.coords)