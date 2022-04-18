from shapely.geometry import LineString

class SimplifiedLinestring:
    def __init__(self, simplified_trip_id:int, 
                line_string:LineString):
        self.simplified_trip_id = simplified_trip_id
        self.line_string = line_string
        self.points = line_string.coords