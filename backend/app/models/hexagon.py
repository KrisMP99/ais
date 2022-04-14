from shapely.geometry import Polygon

class Hexagon:
    def __init__(self, row:int, column:int, hexagon:Polygon):
        self.row = row
        self.column = column
        self.hexagon = hexagon