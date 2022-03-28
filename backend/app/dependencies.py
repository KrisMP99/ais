from dotenv import load_dotenv
from fastapi import Header, HTTPException
import os

load_dotenv()
TOKEN = os.getenv('TOKEN')

async def get_token_header(x_token: str = Header(...)):
    if x_token != TOKEN:
        raise HTTPException(status_code=403, detail="Not authorized")