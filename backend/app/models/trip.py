from array import array
from random import randint
import string
from pandas import Timedelta


def give_color():
            return f'rgb({randint(0, 255)}, {randint(0, 255)}, {randint(0, 255)})'
class Trip:
    def __init__(self, tripId:int, linestring:array, eta:str, shipType:string):
        self.tripId = tripId
        self.linestring = linestring
        self.eta = eta
        self.color = give_color()
        self.shipType = shipType


