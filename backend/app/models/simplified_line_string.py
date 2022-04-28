from shapely.geometry import LineString
from app.models.location import Location
class SimplifiedLineString:
    def __init__(self, simplified_trip_id:int, mmsi:int, type_of_mobile: str, imo: int, name: str, width: float, length: float, ship_type: str,
                line_string:LineString = None, locations:list[Location] = None):
        self.simplified_trip_id = simplified_trip_id
        self.line_string = line_string
        self.locations = locations
        self.mmsi = mmsi

        if type_of_mobile is None:
            self.type_of_mobile = ""
        else:
            self.type_of_mobile = type_of_mobile

        if imo is None:
            self.imo = 0
        else: 
            self.imo = imo

        if name is None:
            self.name = ""
        else: 
            self.name = name
        
        if width is None:
            width = 0
        else: 
            self.width = width
        
        if length is None:
            self.length = 0
        else:
            self.length = length
        
        if ship_type is None:
            self.ship_type = ""
        else:
            self.ship_type = ship_type