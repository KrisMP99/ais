from array import array
import json
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from geoalchemy2 import Geometry
import importlib

USER = os.getenv('POSTGRES_USER')
PASS = os.getenv('POSTGRES_PASSWORD')

Base = automap_base()

SQLALCHEMY_DATABASE_URL = "postgresql://{USER}:{PASS}@db/aisdb"
engine = create_engine( SQLALCHEMY_DATABASE_URL, convert_unicode=True )

Base.prepare(engine, reflrect=True)

GeoJson = Base.classes.spatial_ref_sys
session = Session(engine)

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}

u1 = session.query(GeoJson).first()
print(u1.spatial_ref_sys_collection)