import os
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from app.routers import trips

load_dotenv()
TESTSERVER = os.getenv('TEST_SERVER')
PRODSERVER = os.getenv('PRODUCTION_SERVER')

origins = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    f'http://{TESTSERVER}',
    f'http://{PRODSERVER}'
]

app = FastAPI()

app.include_router(trips.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)