from pydantic import BaseModel
import geojson

class Coordinate(BaseModel):
    lat: float
    long: float