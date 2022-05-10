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
    prefix="/dates",
    tags=["dates"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.get('/dates')
async def get_ship_types():
    print("DDDDD")
    date_dim = Table('date_dim')
    query = Query.from_(date_dim).select(date_dim.date).distinct().where(date_dim.date.notnull())
    loop = asyncio.get_event_loop()
    df = await loop.run_in_executor(None, pd.read_sql_query, str(query), engine)

    if len(df) == 0:
        raise HTTPException(status_code=404, detail='Could not find any dates')

    date_data = df['date'].to_list()
    return jsonable_encoder(date_data)