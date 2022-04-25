from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_token_header, get_logger
from app.db.database import engine, Session
from app.models.coordinate import Coordinate
from app.models.grid_data import GridData
from shapely.geometry.point import Point
from app.models.grid_polygon import GridPolygon
from dotenv import load_dotenv
import shapely.wkb as wkb
import geopandas as gpd
import os

load_dotenv()
API_LOG_FILE_PATH = os.getenv('API_LOG_FILE_PATH')

session = Session()
logger = get_logger(API_LOG_FILE_PATH)

router = APIRouter(
    prefix="/grids",
    tags=["grids"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

grid_sizes_hex = [500, 1000, 2500, 5000, 10000]
grid_sizes_square = [806, 1612, 4030, 8060, 16120]

@router.post('/polygon')
async def get_hexagon(grid_data: GridData):
    gp1 = Point(grid_data.long, grid_data.lat)

    if grid_data.is_hexagon:
        grid_type = "hex"
        if grid_data.grid_size in grid_sizes_hex:
            size = grid_data.grid_size
        else:
            # Throw an error
            print("Yo mama")
    else:
        grid_type = "square"
        if grid_data.grid_size in grid_sizes_square:
            size = grid_data.grid_size
        else:
            # Throw an error
            print("Yo mama") 

    query = f'''
                SELECT
                    d.{grid_type}_{size}_row, 
                    d.{grid_type}_{size}_column, 
                    ST_FlipCoordinates(d.grid_geom) AS geom
                FROM
                    {grid_type}_{size}_dim AS d
                WHERE
                    ST_Within(
                        %(selected_point)s::geometry,
                        d.grid_geom
                    );
            '''

    df = gpd.read_postgis(query, engine, params={'selected_point': wkb.dumps(gp1, hex=True, srid=4326)}, geom_col='geom')
    print(df.head())
    print(df.columns)

    if len(df) == 0:
        logger.error('Could not find the given coordinates')
        raise HTTPException(status_code=404, detail='Could not find the given coordinates')

    poly = GridPolygon(
                row=df.iloc[0].iloc[0], 
                column=df.iloc[0].iloc[1], 
                polygon=df.iloc[0].iloc[2])

    return list(poly.polygon.exterior.coords)