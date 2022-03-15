from pydantic import BaseModel

class Coordinate(BaseModel):
    lat: float
    long: float