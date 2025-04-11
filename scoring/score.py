"""
Scoring calculator used to assign points.

Required as part of a compstate.
"""

from __future__ import annotations

import collections
from typing import Iterable

from sr2025 import (
    DISTRICT_SCORE_MAP,
    DISTRICTS_NO_HIGH_RISE,
    RawDistrict,
    ZONE_COLOURS,
)

TOKENS_PER_ZONE = 6


class InvalidScoresheetException(Exception):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def join_text(strings: Iterable[str], separator: str) -> str:
    """
    Construct an english-language comma separated list ending with the given
    separator word. This enables constructs like "foo, bar and baz" given a list
    of names.

    >>> join_text(["foo", "bar", "baz"], "and")
    "foo, bar and baz"

    >>> join_text(["foo", "bar"], "or")
    "foo or bar"

    >>> join_text(["foo"], "or")
    "foo"
    """
    strings = tuple(strings)

    try:
        *strings, right = strings
    except ValueError:
        return ""

    if not strings:
        return right

    left = ", ".join(strings[:-1])
    return f"{left} {separator} {strings[-1]}"


def join_and(strings: Iterable[str]) -> str:
    return join_text(strings, "and")


def join_or(strings: Iterable[str]) -> str:
    return join_text(strings, "or")


class Scorer:
    def __init__(self, teams_data, arena_data):
        self._teams_data = teams_data
        self._districts = arena_data['other']['districts']

        for district in self._districts.values():
            district['pallets'] = collections.Counter(district['pallets'])
            district['highest'] = district['highest'].replace(' ', '')

    def score_district_for_zone(self, name: str, district: RawDistrict, zone: int) -> int:
        colour = ZONE_COLOURS[zone]

        num_tokens = district['pallets'][colour]
        score = num_tokens * DISTRICT_SCORE_MAP[name]

        if colour in district['highest']:
            # Points are doubled for the team owning the highest pallet
            score *= 2

        return score

    def calculate_scores(self):
        scores = {}

        for tla, info in self._teams_data.items():
            district_score = sum(
                self.score_district_for_zone(name, district, info['zone'])
                for name, district in self._districts.items()
            )
            movement_score = 1 if info.get('left_starting_zone') else 0
            scores[tla] = district_score + movement_score

        return scores

    def validate(self, other_data):
        # Check that the right districts are specified.
        if self._districts.keys() != DISTRICT_SCORE_MAP.keys():
            missing = DISTRICT_SCORE_MAP.keys() - self._districts.keys()
            extra = self._districts.keys() - DISTRICT_SCORE_MAP.keys()
            detail = "Wrong districts specified."
            if missing:
                detail += f" Missing: {join_and(missing)}."
            if extra:
                detail += f" Extra: {join_and(repr(x) for x in extra)}."
            raise InvalidScoresheetException(
                detail,
                code='invalid_districts',
            )

        # Check that the "highest" pallet is a single, valid colour entry.
        bad_highest = {}
        for name, district in self._districts.items():
            highest = district['highest']
            if highest and highest not in ZONE_COLOURS:
                bad_highest[name] = highest
        if bad_highest:
            raise InvalidScoresheetException(
                f"Invalid pallets specified as the highest in some districts -- "
                f"must be a single pallet from "
                f"{join_or(repr(x) for x in ZONE_COLOURS)}.\n"
                f"{bad_highest!r}",
                code='invalid_highest_pallet',
            )

        # Check that the pallets are valid colours.
        bad_pallets = {}
        for name, district in self._districts.items():
            extra = district['pallets'].keys() - ZONE_COLOURS
            if extra:
                bad_pallets[name] = extra
        if bad_pallets:
            raise InvalidScoresheetException(
                f"Invalid pallets specified in some districts -- must be from "
                f"{join_or(repr(x) for x in ZONE_COLOURS)}.\n"
                f"{bad_pallets!r}",
                code='invalid_pallets',
            )

        # Check that the "highest" pallet is accompanied by at least one pallet
        # of that colour in the district.
        bad_highest2 = {}
        for name, district in self._districts.items():
            highest = district['highest']
            if highest and not district['pallets'][highest]:
                bad_highest2[name] = (highest, district['pallets'].keys())
        if bad_highest2:
            detail = "\n".join(
                (
                    (
                        f"District {name} has only {join_and(pallets)} so "
                        f"{highest!r} cannot be the highest."
                    )
                    if pallets
                    else (
                        f"District {name} has no pallets so {highest!r} cannot "
                        "be the highest."
                    )
                )
                for name, (highest, pallets) in bad_highest2.items()
            )
            raise InvalidScoresheetException(
                f"Impossible pallets specified as the highest in some districts "
                f"-- must be a pallet which is present in the district.\n"
                f"{detail}",
                code='impossible_highest_pallet',
            )

        # Check that the "highest" pallet in districts which don't have a
        # high-rise has another pallet to be placed on top of (pallets on the
        # floor don't qualify for being the highest).
        single_pallet_highest = {}
        for name in DISTRICTS_NO_HIGH_RISE:
            district = self._districts[name]
            highest = district['highest']
            num_pallets = sum(district['pallets'].values())
            if num_pallets == 1 and highest:
                single_pallet_highest[name] = highest
        if single_pallet_highest:
            raise InvalidScoresheetException(
                "Districts without a high-rise and only a single pallet cannot "
                "have a \"highest\" pallet since pallets on the floor cannot "
                "count as the highest.\n"
                f"{single_pallet_highest!r}",
                code='impossible_highest_single_pallet',
            )

        # Check that the total number of pallets of each colour across the whole
        # arena are less than the expected number.
        totals = collections.Counter()
        for district in self._districts.values():
            totals += district['pallets']
        bad_totals = [x for x, y in totals.items() if y > TOKENS_PER_ZONE]
        if bad_totals:
            raise InvalidScoresheetException(
                f"Too many {join_and(repr(x) for x in bad_totals)} pallets "
                f"specified, must be no more than {TOKENS_PER_ZONE} of each type.\n"
                f"Totals: {totals!r}",
                code='too_many_pallets',
            )


if __name__ == '__main__':
    import libproton
    libproton.main(Scorer)
