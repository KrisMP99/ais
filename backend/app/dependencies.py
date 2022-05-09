from dotenv import load_dotenv
from fastapi import Header, HTTPException
import logging
import os

load_dotenv()
TOKEN = os.getenv('TOKEN')

async def get_token_header(x_token: str = Header(...)):
    if x_token != TOKEN:
        raise HTTPException(status_code=403, detail="Not authorized")

def get_logger(path):
    Log_Format = "[%(levelname)s] -  %(asctime)s - %(message)s"
    logging.basicConfig(format = Log_Format,
                        force = True,
                        handlers = [
                            logging.FileHandler(path),
                            logging.StreamHandler()
                        ],
                        level = logging.INFO)

    logger = logging.getLogger()
    return logger