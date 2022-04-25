from shapely.geometry import Point

class Location:
    def __init__(self, hex_10000_row:int, 
                hex_10000_column:int, location:Point,
                date_id:int, time_id:int, ship_type: str,
                sog:float):
        self.hex_10000_row = hex_10000_row
        self.hex_10000_column = hex_10000_column
        self.location = location
        self.date_id = date_id
        self.time_id = time_id
        self.ship_type = ship_type
        self.sog = sog