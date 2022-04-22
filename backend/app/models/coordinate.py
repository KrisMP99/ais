from pydantic import BaseModel

class Coordinate(BaseModel):
    long: float
    lat: float