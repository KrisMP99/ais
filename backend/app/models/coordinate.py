from pydantic import BaseModel

class Coordinate(BaseModel):
    long: float
    lat: float
    is_hexagon: bool
    grid_size: int