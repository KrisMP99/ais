from shapely.geometry import Point

class Location:
    def __init__(self, row:int, 
                column:int, location:Point,
                date_id:int, time_id:int,
                sog:float):
        self.row = row
        self.column = column
        self.location = location
        self.date_id = date_id
        self.time_id = time_id
        self.sog = sog