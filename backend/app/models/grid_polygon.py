from shapely.geometry import Polygon, Point

class GridPolygon:
    def __init__(self, row:int, column:int, polygon:Polygon, centroid:Point=None):
        self.row = row
        self.column = column
        self.polygon = polygon
        self.centroid = centroid