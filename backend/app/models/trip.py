from array import array
from random import randint
import string
from pandas import Timedelta


def give_color():
            return f'rgb({randint(0, 255)}, {randint(0, 255)}, {randint(0, 255)})'
class Trip:
    def __init__(self, trip_id:int, line_string:array, eta:str, ship_type:string, mmsi:int, imo:int, type_of_mobile:str, name:str, width:float, length:float):
        self.trip_id = trip_id
        self.line_string = line_string
        self.eta = eta
        self.color = give_color()
        self.ship_Type = ship_type
        self.mmsi = mmsi
        self.imo = imo
        self.type_of_mobile = type_of_mobile
        self.name = name,
        self.width = width,
        self.length = length



