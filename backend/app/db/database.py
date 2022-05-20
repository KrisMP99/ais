import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')

SQLALCHEMY_DATABASE_URL = f'postgresql://postgres:admin@host.docker.internal/aisdb'
engine = create_engine(SQLALCHEMY_DATABASE_URL, convert_unicode=True )

Session = sessionmaker(bind=engine)