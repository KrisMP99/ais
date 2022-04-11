from shapely.geometry import Polygon

class Hexagon:
    def __init__(self, hid:int, geom:Polygon):
        self.hid = hid
        self.geom = geom