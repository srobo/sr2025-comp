"""
Scoring calculator used to assign points.

Required as part of a compstate.
"""

from __future__ import annotations

import collections
import warnings

from sr2025 import DISTRICT_SCORE_MAP, RawDistrict, ZONE_COLOURS


class District(RawDistrict):
    pallet_counts: collections.Counter[str]


class InvalidScoresheetException(Exception):
    def __init__(self, message: str, *, code: str) -> None:
        super().__init__(message)
        self.code = code


class Scorer:
    def __init__(self, teams_data, arena_data):
        self._teams_data = teams_data
        self._districts = arena_data['other']['districts']

        for district in self._districts.values():
            district['pallet_counts'] = collections.Counter(
                district['pallets'].replace(' ', ''),
            )

    def score_district_for_zone(self, name: str, district: District, zone: int) -> int:
        colour = ZONE_COLOURS[zone]

        num_tokens = district['pallet_counts'][colour]
        score = num_tokens * DISTRICT_SCORE_MAP[name]

        if colour in district['highest']:
            # Points are doubled for the team owning the highest pallet
            score * 2

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
        warnings.warn("Scoresheet validation not implemented")


if __name__ == '__main__':
    import libproton
    libproton.main(Scorer)
