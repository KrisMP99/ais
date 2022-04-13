from shapely.geometry import LineString

class Linestring:
    def __init__(self, trip_id:int, simplified_trip_id:int, 
                line_string:LineString): 
        self.trip_id = trip_id
        simplified_trip_id = simplified_trip_id
        line_string = line_string
        points = line_string.coords