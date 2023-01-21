from __future__ import annotations


class Point:

    __slots__ = (
        'ally',
        'enemy'
    )

    def __init__(self, ally: int, enemy: int):
        self.ally = ally
        self.enemy = enemy

    def __add__(self, other: Point) -> Point:
        return Point(self.ally+other.ally, self.enemy+other.enemy)

    def __sub__(self, other: Point) -> Point:
        return Point(self.ally-other.ally, self.enemy-other.enemy)

    def __str__(self):
        return f'{self.ally} : {self.enemy}'

    def __bool__(self):
        return not (self.ally == 0 and self.enemy == 0)
