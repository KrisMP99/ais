from pydantic import BaseModel
import geojson

class Coordinate(BaseModel):
    long: float
    lat: float