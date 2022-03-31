import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()
USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')
DBNAME = os.getenv('DB_NAME')

SQLALCHEMY_DATABASE_URL = f'postgresql://{USER}:{PASS}@db/{DBNAME}'
engine = create_engine( SQLALCHEMY_DATABASE_URL, convert_unicode=True )

Session = sessionmaker(bind=engine)