""" Typings for type validation and documentation """

from typing import TypedDict


class SearchStatus(TypedDict):
    mon: int
    table: str
    year: int


class SearchTime(TypedDict):
    year: int
    mon: int
    day: int
    hour: int
    min: int
    sec: int


class SearchFile(TypedDict):
    StartTime: SearchTime
    EndTime: SearchTime
    frameRate: int
    height: int
    name: str
    size: int
    type: str
    width: int
