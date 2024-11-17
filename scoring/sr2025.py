from __future__ import annotations

from typing import TypedDict


class RawDistrict(TypedDict):
    highest: str
    pallets: str


DISTRICT_SCORE_MAP = {
    'outer_nw': 1,
    'outer_ne': 1,
    'outer_se': 1,
    'outer_sw': 1,
    'inner_nw': 2,
    'inner_ne': 2,
    'inner_se': 2,
    'inner_sw': 2,
    'central': 3,
}

DISTRICTS_NO_HIGH_RISE = frozenset([
    'outer_nw',
    'outer_ne',
    'outer_se',
    'outer_sw',
])

DISTRICTS = DISTRICT_SCORE_MAP.keys()

assert DISTRICTS_NO_HIGH_RISE < DISTRICTS

ZONE_COLOURS = (
    'G',    # zone 0 = green
    'O',    # zone 1 = orange
    'P',    # zone 2 = purple
    'Y',    # zone 3 = yellow
)
