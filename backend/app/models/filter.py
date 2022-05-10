from pydantic import BaseModel


class Filter(BaseModel):
    ship_types: list[str]  | None
    nav_stats: list[str] | None
    direction: bool | None
    date_range: list[int] | None