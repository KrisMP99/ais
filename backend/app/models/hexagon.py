from shapely.geometry import Polygon, Point

class Hexagon:
    def __init__(self, row:int, column:int, hexagon:Polygon, centroid:Point):
        self.row = row
        self.column = column
        self.hexagon = hexagon
        self.centroid = centroid