from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_token_header, get_logger
from app.db.database import engine, Session
from pypika import Query, Field, Table
from fastapi.encoders import jsonable_encoder
from dotenv import load_dotenv
import asyncio
import pandas as pd
import os

load_dotenv()
API_LOG_FILE_PATH = os.getenv('API_LOG_FILE_PATH')

session = Session()
logger = get_logger(API_LOG_FILE_PATH)

router = APIRouter(
    prefix="/navigational_attributes",
    tags=["navigational_attributes"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.get('/nav-attrs')
async def get_ship_types():
    nav_dim = Table('nav_dim')
    query = Query.from_(nav_dim).select(nav_dim.navigational_status).distinct().where(nav_dim.navigational_status.notnull())
    loop = asyncio.get_event_loop()
    df = await loop.run_in_executor(None, pd.read_sql_query, str(query), engine)

    if len(df) == 0:
        raise HTTPException(status_code=404, detail='Could not find any nav statuses')

    nav_stats = df['navigational_status'].to_list()
    return jsonable_encoder(nav_stats)