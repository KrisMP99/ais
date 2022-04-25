import os
from venv import create
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from app.routers import trips, grids, ship_attributes

load_dotenv()
TESTSERVER = os.getenv('TEST_SERVER')
PRODSERVER = os.getenv('PRODUCTION_SERVER')

origins = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    f'http://{TESTSERVER}',
    f'http://{PRODSERVER}',
]

middleware = [
    Middleware(
        CORSMiddleware, 
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['POST','PUT','GET'],
        allow_headers=['*']
    )
]

app = FastAPI(middleware=middleware)
app.include_router(trips.router)
app.include_router(grids.router)
app.include_router(ship_attributes.router)