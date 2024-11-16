"""
Scoring calculator used to assign points.

Required as part of a compstate.
"""

from __future__ import annotations

import collections
from typing import Iterable

from sr2025 import DISTRICT_SCORE_MAP, RawDistrict, ZONE_COLOURS

TOKENS_PER_ZONE = 6


class District(RawDistrict):
    pallet_counts: collections.Counter[str]


class InvalidScoresheetException(Exception):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


def join_text(strings: Iterable[str], separator: str) -> str:
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
            district['pallet_counts'] = collections.Counter(
                district['pallets'].replace(' ', ''),
            )
            district['highest'] = district['highest'].replace(' ', '')

    def score_district_for_zone(self, name: str, district: District, zone: int) -> int:
        colour = ZONE_COLOURS[zone]

        num_tokens = district['pallet_counts'][colour]
        score = num_tokens * DISTRICT_SCORE_MAP[name]

        if colour in district['highest']:
            # Points are doubled for the team owning the highest pallet
            score *= 2

        return score

    def calculate_scores(self):
        scores = {}

        for tla, info in self._teams_data.items():
            scores[tla] = sum(
                self.score_district_for_zone(name, district, info['zone'])
                for name, district in self._districts.items()
            )

        return scores

    def validate(self, other_data):
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

        bad_pallets = {}
        for name, district in self._districts.items():
            extra = district['pallet_counts'].keys() - ZONE_COLOURS
            if extra:
                bad_pallets[name] = extra
        if bad_pallets:
            raise InvalidScoresheetException(
                f"Invalid pallets specified in some districts -- must be from "
                f"{join_or(repr(x) for x in ZONE_COLOURS)}.\n"
                f"{bad_pallets!r}",
                code='invalid_pallets',
            )

        bad_highest2 = {}
        for name, district in self._districts.items():
            highest = district['highest']
            if highest and highest not in district['pallet_counts']:
                bad_highest2[name] = (highest, district['pallet_counts'].keys())
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

        missing_highest = {}
        for name, district in self._districts.items():
            highest = district['highest']
            pallet_counts = district['pallet_counts']
            if len(pallet_counts) == 1 and not highest:
                pallet, = pallet_counts.keys()
                missing_highest[name] = pallet
        if missing_highest:
            raise InvalidScoresheetException(
                f"Some districts with pallets from a single team are missing "
                "specification of the highest.\n"
                f"{missing_highest!r}",
                code='missing_highest_pallet',
            )

        totals = collections.Counter()
        for district in self._districts.values():
            totals += district['pallet_counts']
        if any(x > TOKENS_PER_ZONE for x in totals.values()):
            raise InvalidScoresheetException(
                f"Too many pallets of some kinds specified, must be no more "
                f"than {TOKENS_PER_ZONE} of each type.\n"
                f"{totals!r}",
                code='too_many_pallets',
            )


if __name__ == '__main__':
    import libproton
    libproton.main(Scorer)
