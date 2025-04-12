#!/usr/bin/env python3

"""
Tests for the scoring logic.

Not really part of a compstate, though the SRComp validation GitHub Action will
auto detect this and run the tests.
"""

import copy
import pathlib
import random
import sys
import unittest

import yaml

# Path hackery
ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from score import (  # type: ignore[import-not-found]  # noqa: E402
    InvalidScoresheetException,
    Scorer,
)
from sr2025 import (  # type: ignore[import-not-found]  # noqa: E402
    DISTRICTS,
    RawDistrict,
)


def shuffled(text: str) -> str:
    values = list(text)
    random.shuffle(values)
    return ''.join(values)


class ScorerTests(unittest.TestCase):
    longMessage = True

    def construct_scorer(self, districts):
        return Scorer(
            self.teams_data,
            {'other': {'districts': districts}},
        )

    def assertScores(self, expected_scores, districts):
        scorer = self.construct_scorer(districts)
        scorer.validate(None)
        actual_scores = scorer.calculate_scores()

        self.assertEqual(expected_scores, actual_scores, "Wrong scores")

    def assertInvalidScoresheet(self, districts, *, code):
        scorer = self.construct_scorer(districts)

        with self.assertRaises(InvalidScoresheetException) as cm:
            scorer.validate(None)

        self.assertEqual(
            code,
            cm.exception.code,
            f"Wrong error code, message was: {cm.exception}",
        )

    def setUp(self) -> None:
        self.teams_data = {
            'GGG': {'zone': 0, 'present': True, 'left_starting_zone': False},
            'OOO': {'zone': 1, 'present': True, 'left_starting_zone': False},
        }
        self.districts: dict[str, RawDistrict] = {
            name: RawDistrict({
                'highest': '',
                'pallets': {},
            })
            for name in DISTRICTS
        }

    def test_template(self):
        template_path = ROOT / 'template.yaml'
        with template_path.open() as f:
            data = yaml.safe_load(f)

        teams_data = data['teams']
        arena_data = data.get('arena_zones')
        extra_data = data.get('other')

        scorer = Scorer(teams_data, arena_data)
        scores = scorer.calculate_scores()

        scorer.validate(extra_data)

        self.assertEqual(
            teams_data.keys(),
            scores.keys(),
            "Should return score values for every team",
        )

    # Scoring logic

    def test_left_starting_zone(self) -> None:
        self.teams_data['GGG']['left_starting_zone'] = True
        self.assertScores(
            {
                'GGG': 1,
                'OOO': 0,
            },
            self.districts,
        )

    def test_outer_single(self) -> None:
        self.districts['outer_nw']['pallets'] = {'G': 1}
        self.assertScores(
            {
                'GGG': 1,
                'OOO': 0,
            },
            self.districts,
        )

    def test_outer_multiple(self) -> None:
        self.districts['outer_nw']['pallets'] = {'G': 2, 'O': 1}
        self.assertScores(
            {
                'GGG': 2,
                'OOO': 1,
            },
            self.districts,
        )

    def test_outer_highest(self) -> None:
        self.districts['outer_nw']['highest'] = 'G'
        self.districts['outer_nw']['pallets'] = {'G': 2, 'O': 1}
        self.assertScores(
            {
                'GGG': 4,
                'OOO': 1,
            },
            self.districts,
        )

    def test_outer_highest_self(self) -> None:
        self.districts['outer_nw']['highest'] = 'G'
        self.districts['outer_nw']['pallets'] = {'G': 2}
        self.assertScores(
            {
                'GGG': 4,
                'OOO': 0,
            },
            self.districts,
        )

    def test_outer_highest_use_other_team(self) -> None:
        self.districts['outer_nw']['highest'] = 'G'
        self.districts['outer_nw']['pallets'] = {'G': 1, 'O': 1}
        self.assertScores(
            {
                'GGG': 2,
                'OOO': 1,
            },
            self.districts,
        )

    def test_inner_single(self) -> None:
        self.districts['inner_ne']['pallets'] = {'O': 1}
        self.assertScores(
            {
                'GGG': 0,
                'OOO': 2,
            },
            self.districts,
        )

    def test_inner_multiple(self) -> None:
        self.districts['inner_ne']['pallets'] = {'G': 1, 'O': 2}
        self.assertScores(
            {
                'GGG': 2,
                'OOO': 4,
            },
            self.districts,
        )

    def test_inner_highest(self) -> None:
        self.districts['inner_ne']['highest'] = 'O'
        self.districts['inner_ne']['pallets'] = {'G': 1, 'O': 2}
        self.assertScores(
            {
                'GGG': 2,
                'OOO': 8,
            },
            self.districts,
        )

    def test_central_single(self) -> None:
        self.districts['central']['pallets'] = {'O': 1}
        self.assertScores(
            {
                'GGG': 0,
                'OOO': 3,
            },
            self.districts,
        )

    def test_central_multiple(self) -> None:
        self.districts['central']['pallets'] = {'G': 1, 'O': 2}
        self.assertScores(
            {
                'GGG': 3,
                'OOO': 6,
            },
            self.districts,
        )

    def test_central_highest(self) -> None:
        self.districts['central']['highest'] = 'O'
        self.districts['central']['pallets'] = {'G': 1, 'O': 2}
        self.assertScores(
            {
                'GGG': 3,
                'OOO': 12,
            },
            self.districts,
        )

    def test_mixed(self) -> None:
        self.teams_data['OOO']['left_starting_zone'] = True
        self.districts['outer_sw']['pallets'] = {'O': 1}
        self.districts['inner_sw']['pallets'] = {'G': 1}
        self.districts['central']['pallets'] = {'G': 1, 'O': 1}
        self.assertScores(
            {
                'GGG': 5,
                'OOO': 5,
            },
            self.districts,
        )

    def test_mixed_highest(self) -> None:
        self.districts['outer_sw']['pallets'] = {'O': 1}
        self.districts['inner_sw']['highest'] = 'G'
        self.districts['inner_sw']['pallets'] = {'G': 1}
        self.districts['central']['highest'] = 'G'
        self.districts['central']['pallets'] = {'G': 1, 'O': 1}
        self.assertScores(
            {
                'GGG': 10,
                'OOO': 4,
            },
            self.districts,
        )

    def test_outer_single_token_highest(self) -> None:
        # Tokens *can* be placed on top of other tokens which themselves aren't
        # counted as in the zone.
        self.districts['outer_nw']['highest'] = 'G'
        self.districts['outer_nw']['pallets'] = {'G': 1}
        self.assertScores(
            {
                'GGG': 2,
                'OOO': 0,
            },
            self.districts,
        )

    # Invalid input

    def test_bad_highest_pallet_letter(self) -> None:
        self.districts['outer_sw']['highest'] = 'o'
        self.assertInvalidScoresheet(
            self.districts,
            code='invalid_highest_pallet',
        )

    def test_bad_pallet_letter(self) -> None:
        self.districts['outer_sw']['pallets'] = {'o': 1}
        self.assertInvalidScoresheet(
            self.districts,
            code='invalid_pallets',
        )

    def test_missing_district(self) -> None:
        del self.districts['outer_sw']
        self.assertInvalidScoresheet(
            self.districts,
            code='invalid_districts',
        )

    def test_extra_district(self) -> None:
        self.districts['bees'] = copy.deepcopy(self.districts['central'])
        self.assertInvalidScoresheet(
            self.districts,
            code='invalid_districts',
        )

    # Tolerable input deviances

    def test_spacey(self) -> None:
        self.districts['outer_nw']['highest'] = '  O '
        self.districts['outer_nw']['pallets'] = {'G': 1, 'O': 1, 'Y': 1}
        self.assertScores(
            {
                'GGG': 1,
                'OOO': 2,
            },
            self.districts,
        )

    # Impossible scenarios

    def test_highest_when_no_pallets(self) -> None:
        self.districts['outer_sw']['highest'] = 'O'
        self.assertInvalidScoresheet(
            self.districts,
            code='impossible_highest_pallet',
        )

    def test_highest_when_no_pallets_that_zone(self) -> None:
        self.districts['outer_sw']['highest'] = 'Y'
        self.districts['outer_sw']['pallets'] = {'O': 1, 'P': 1}
        self.assertInvalidScoresheet(
            self.districts,
            code='impossible_highest_pallet',
        )

    def test_highest_when_zero_pallets_that_zone(self) -> None:
        self.districts['outer_sw']['highest'] = 'Y'
        self.districts['outer_sw']['pallets'] = {'O': 1, 'P': 1, 'G': 0, 'Y': 0}
        self.assertInvalidScoresheet(
            self.districts,
            code='impossible_highest_pallet',
        )

    def test_too_many_pallets(self) -> None:
        self.districts['outer_sw']['pallets'] = {'G': 7, 'O': 1}
        self.assertInvalidScoresheet(
            self.districts,
            code='too_many_pallets',
        )


if __name__ == '__main__':
    unittest.main()
