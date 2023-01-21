from __future__ import annotations
from typing import Optional

from enum import Enum


class Status(Enum):

    def __str__(self):
        return self._name_

    @property
    def en(self) -> str:
        return self.value[0]

    @property
    def ja(self) -> str:
        return self.value[1]

    @staticmethod
    def from_string(text: str) -> Optional[Status]:
        for status in Status:
            if text in status.value:
                return status
        return None

    ONGOING = ('Ongoing','進行中')
    ARCHIVE = ('Archive','アーカイブ')
    FINISHED = ('Result','リザルト')
