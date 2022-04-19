from shapely.geometry import LineString
from app.models.location import Location
class SimplifiedLineString:
    def __init__(self, simplified_trip_id:int, 
                line_string:LineString = None, locations:list[Location] = None):
        self.simplified_trip_id = simplified_trip_id
        self.line_string = line_string
        self.locations = locations