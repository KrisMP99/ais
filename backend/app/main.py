import os
from fastapi import FastAPI
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from app.routers import trips

load_dotenv()
TESTSERVER = os.getenv('TEST_SERVER')
PRODSERVER = os.getenv('PRODUCTION_SERVER')
ORIG = os.getenv('ORIGIN_ONE')
ORIG2 = os.getenv('ORIGIN_TWO')

app = FastAPI()

app.include_router(trips.router)

origins = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    f'http://{TESTSERVER}:3000',
    f'http://{PRODSERVER}:3000'
]

app = CORSMiddleware(
    app=app,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
	allow_headers=["*"],
)