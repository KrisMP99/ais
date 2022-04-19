from shapely.geometry import Point

class Location:
    def __init__(self, hex_10000_row:int, 
                hex_10000_column:int, location:Point):
        self.hex_10000_row = hex_10000_row
        self.hex_10000_column = hex_10000_column
        self.location = location