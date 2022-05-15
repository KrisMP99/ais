from random import randint
from app.models.filter import Filter
from fastapi import APIRouter, Depends
from app.dependencies import get_token_header, get_logger
from app.models.coordinate import Coordinate
from app.models.grid_polygon import GridPolygon
from app.db.database import Session
from app.db.queries.trip_queries import get_polygons, get_line_strings
from shapely.geometry import Point
from dotenv import load_dotenv
import pandas as pd
import os
import numpy as np

load_dotenv()
API_LOG_FILE_PATH = os.getenv('API_LOG_FILE_PATH')

session = Session()
logger = get_logger(API_LOG_FILE_PATH)
router = APIRouter(
    prefix="/trips",
    tags=["trips"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.post('/')
async def get_trips(p1: Coordinate, p2: Coordinate, filter: Filter):
    gp1 = Point(p1.long, p1.lat)
    gp2 = Point(p2.long, p2.lat)

    # First we fetch the hexagons for where two points can be found inside
    logger.info('Fetching polygons...')

    # The check of the p1.is_hexagon and p1.grid_size should probably be in a function on its own
    # and then returned to here, to be given to the function call
    poly_df = get_polygons(gp1, gp2, p1.is_hexagon, p1.grid_size, logger)
    pd.options.display.max_colwidth = 10000
    
    # We add the hexagons to a list, so that we can access these values later
    polygons_list = add_polygons_to_list(poly_df)
    logger.info('Polygons fetched!')
    
    logger.info('Fetching line strings')
    df = get_line_strings(poly1=polygons_list[0], poly2=polygons_list[1], filter=filter, logger=logger)
    # with open('/srv/data/csv/line_strings.json', 'w') as out_file:
    #     out_file.write(df.to_json())

    # Do the ETA calculations

    df['df_loc1_time_id'] = pd.to_datetime(df['df_loc1_time_id'].astype(str).str.zfill(6), format="%H%M%S")
    df['df_loc2_time_id'] = pd.to_datetime(df['df_loc2_time_id'].astype(str).str.zfill(6), format="%H%M%S")
    
    df['direction'] = np.where(df['df_loc1_time_id'] < df['df_loc2_time_id'], ('Forward'), ('Backwards'))

    if(filter.direction):
        df = df[df['direction'] == 'Forward']
    elif(filter.direction is not None):
        df = df[df['direction'] == 'Backwards']

    df['c1_time'] = (pd.to_timedelta((df['dist_df_loc1_c1'] / df['df_loc1_sog']),unit='s') + df['df_loc1_time_id'])
    df['c2_time'] = (pd.to_timedelta((df['dist_df_loc2_c2'] / df['df_loc2_sog']),unit='s') + df['df_loc2_time_id'])

    df['c1_time'], df['c2_time'] = np.where(df['c1_time'] < df['c2_time'], (df['c1_time'], df['c2_time']), (df['c2_time'], df['c1_time']))

    
    df['eta'] = (df['c2_time'] - df['c1_time']).dt.floor('s')

    df = df.sort_values(by=['eta'])
    df['eta_min'] = str(df['eta'].min()).split("0 days")[-1]
    df['eta_median'] = str(df['eta'].median()).split("0 days")[-1]
    df['eta_max'] = str(df['eta'].max()).split("0 days")[-1]
    df['eta_avg'] = str(df['eta'].mean()).split("0 days")[-1].split(".")[0]
    df['eta'] = df['eta'].astype(str).str.split("0 days").str[-1]

    df = df.drop(columns=['df_loc1', 'df_loc1_time_id', 'df_loc1_sog', 'dist_df_loc1_c1', 'df_loc2', 'df_loc2_time_id', 'df_loc2_sog', 'dist_df_loc2_c2', 'c1_time', 'c2_time'],axis=1, errors='ignore')
    logger.info('Line strings fetched!')
    
    df['color'] = df.apply(lambda x: give_color(), axis=1)

    return df.to_json()

def add_polygons_to_list(df: pd.DataFrame) -> list[GridPolygon]:
    import shapely.wkb as wkb
    polygons = []
    
    for table_row in df.itertuples(name=None):
        print("Polygon:", wkb.dumps(table_row[3], hex=True, srid=4326))
        print("Centroid:", table_row[4])
        polygons.append(GridPolygon(column=table_row[2], row=table_row[1], polygon=table_row[3], centroid=table_row[4]))
    return polygons

def give_color():
    return f'rgb({randint(0, 255)}, {randint(0, 255)}, {randint(0, 255)})'