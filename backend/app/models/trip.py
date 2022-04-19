import string
from pandas import Timedelta
from shapely.geometry import LineString

class Trip:
    def __init__(self, tripId:int, linestring:LineString, eta:Timedelta, color:string, shipType:string):
        self.tripId = tripId
        self.linestring = linestring
        self.eta = eta
        self.color = color
        self.shipType = shipType