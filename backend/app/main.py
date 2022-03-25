import os
from venv import create
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from app.routers import trips

load_dotenv()
TESTSERVER = os.getenv('TEST_SERVER')
TESTSERVERNOPORT = os.getenv('TEST_SERVER_NO_PORT')
PRODSERVER = os.getenv('PRODUCTION_SERVER')
PRODSERVERNOPORT = os.getenv('PRODUCTION_SERVER_NO_PORT')

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
        allow_methods=['*'],
        allow_headers=['*']
    )
]

app = FastAPI(middleware=middleware)
app.include_router(trips.router)