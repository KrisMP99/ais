from pydantic import BaseModel
from app.models.coordinate import Coordinate

class Polygon(BaseModel):
    p1: Coordinate
    p2: Coordinate
    p3: Coordinate
    p4: Coordinate
    p5: Coordinate
    p6: Coordinate
    p7: Coordinate