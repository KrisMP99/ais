from pydantic import BaseModel

class GridData(BaseModel):
    long: float
    lat: float
    is_hexagon: bool
    grid_size: int