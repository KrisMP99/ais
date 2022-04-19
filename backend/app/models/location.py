from shapely.geometry import Point

class Location:
    def __init__(self, hex_10000_row:int, 
                hex_10000_column:int, location:Point,
                date_dim_id:int, time_dim_id:int, ship_type: str,
                sog:float):
        self.hex_10000_row = hex_10000_row
        self.hex_10000_column = hex_10000_column
        self.location = location
        self.date_dim_id = date_dim_id
        self.time_dim_id = time_dim_id
        self.ship_type = ship_type
        self.sog = sog