from array import array
from pydantic import BaseModel


class Filter(BaseModel):
    ship_types: list[str]
        # self.date_range = date_range