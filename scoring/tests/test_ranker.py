#!/usr/bin/env python3

"""
Tests for the points override logic.
"""

from __future__ import annotations

import pathlib
import sys
import unittest
from typing import Collection, Mapping

from league_ranker import RankedPosition, TZone
from sr.comp.types import ArenaName, MatchNumber

# Path hackery
ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from ranker import calc_ranked_points  # type: ignore[import-not-found]  # noqa: E402


class RankerTests(unittest.TestCase):
    def assertPoints(
        self,
        expected_points: dict[TZone, int],
        positions: Mapping[int, Collection[TZone]],
        *,
        disqualifications: Collection[TZone] = (),
        match_num: int,
    ) -> None:
        actual_points = calc_ranked_points(
            {RankedPosition(x): y for x, y in positions.items()},
            disqualifications=disqualifications,
            num_zones=len(expected_points),
            match_id=(ArenaName('main'), MatchNumber(match_num)),
        )

        self.assertEqual(expected_points, actual_points, "Wrong points")

    def test_virtual_league_match(self) -> None:
        self.assertPoints(
            expected_points={
                'ABC': 8,
                'DEF': 6,
                'GHI': 4,
                'JKL': 2,
            },
            positions={
                1: ('ABC',),
                2: ('DEF',),
                3: ('GHI',),
                4: ('JKL',),
            },
            match_num=0,
        )

    def test_virtual_league_match_with_tie(self) -> None:
        self.assertPoints(
            expected_points={
                'ABC': 8,
                'DEF': 5,
                'GHI': 5,
                'JKL': 2,
            },
            positions={
                1: ('ABC',),
                2: ('DEF', 'GHI'),
                4: ('JKL',),
            },
            match_num=0,
        )

    def test_physical_league_match(self) -> None:
        self.assertPoints(
            expected_points={
                'ABC': 16,
                'DEF': 12,
                'GHI': 8,
                'JKL': 4,
            },
            positions={
                1: ('ABC',),
                2: ('DEF',),
                3: ('GHI',),
                4: ('JKL',),
            },
            match_num=50,
        )

    def test_physical_league_match_with_tie(self) -> None:
        self.assertPoints(
            expected_points={
                'ABC': 16,
                'DEF': 10,
                'GHI': 10,
                'JKL': 4,
            },
            positions={
                1: ('ABC',),
                2: ('DEF', 'GHI'),
                4: ('JKL',),
            },
            match_num=50,
        )

    def test_knockouts_match(self) -> None:
        self.assertPoints(
            expected_points={
                'ABC': 16,
                'DEF': 12,
                'GHI': 8,
                'JKL': 4,
            },
            positions={
                1: ('ABC',),
                2: ('DEF',),
                3: ('GHI',),
                4: ('JKL',),
            },
            match_num=150,
        )

    def test_knockouts_match_with_tie(self) -> None:
        self.assertPoints(
            expected_points={
                'ABC': 16,
                'DEF': 10,
                'GHI': 10,
                'JKL': 4,
            },
            positions={
                1: ('ABC',),
                2: ('DEF', 'GHI'),
                4: ('JKL',),
            },
            match_num=150,
        )


if __name__ == '__main__':
    unittest.main()
