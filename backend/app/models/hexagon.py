from shapely.geometry import Polygon

class Hexagon:
    def __init__(self, column:int, row:int, geom:Polygon):
        self.column = column
        self.row = row
        self.geom = geom