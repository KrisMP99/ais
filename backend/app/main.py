import os
from venv import create
from fastapi import FastAPI
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
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

def create_app() -> CORSMiddleware:
    """Create app wrapper to overcome middleware issues."""
    fastapi_app = FastAPI()
    app.include_router(trips.router)
    return CORSMiddleware(
        fastapi_app,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['*'],
        allow_headers=['*'],
    )

app = create_app()