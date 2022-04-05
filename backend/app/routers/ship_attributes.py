from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_token_header, get_logger
from app.db.database import engine, Session
from pypika import Query
from fastapi.encoders import jsonable_encoder
import asyncio
import pandas as pd

session = Session()
logger = get_logger()
router = APIRouter(
    prefix="/ship_attributes",
    tags=["ship_attributes"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

@router.get('/ship-types')
async def get_ship_types():
    query = Query.from_('ship_type_dim').select('ship_type').distinct() 
    loop = asyncio.get_event_loop()
    df = await loop.run_in_executor(None, pd.read_sql_query, str(query), engine)

    if len(df) == 0:
        raise HTTPException(status_code=404, detail='Could not find any ship types')

    ship_types = df['ship_type'].to_list()
    return jsonable_encoder(ship_types)