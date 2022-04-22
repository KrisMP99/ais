from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_token_header, get_logger
from app.db.database import engine, Session
from app.models.coordinate import Coordinate
from shapely.geometry.point import Point
from app.models.hexagon import Hexagon
from dotenv import load_dotenv
import shapely.wkb as wkb
import geopandas as gpd
import os

load_dotenv()
API_LOG_FILE_PATH = os.getenv('API_LOG_FILE_PATH')

session = Session()
logger = get_logger(API_LOG_FILE_PATH)

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
                    ST_FlipCoordinates(h.grid_geom) AS geom
                FROM
                    hex_10000_dim AS h
                WHERE
                    ST_Within(
                        %(hexagon)s::geometry,
                        h.geom
                    );
            '''

    df = gpd.read_postgis(query, engine, params={'hexagon': wkb.dumps(gp1, hex=True, srid=4326)}, geom_col='geom')

    if len(df) == 0:
        logger.error('Could not find the given coordinates')
        raise HTTPException(status_code=404, detail='Could not find the given coordinates')


    hex = Hexagon(
                row=df.hex_10000_row.iloc[0], 
                column=df.hex_10000_column.iloc[0], 
                hexagon=df.hexagon.iloc[0],
                centroid=df.centroid.iloc[0])
    return list(hex.hexagon.exterior.coords)