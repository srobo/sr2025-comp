#!/usr/bin/env python3

"""
Tests for the scoring logic.

Not really part of a compstate, though the SRComp validation GitHub Action will
auto detect this and run the tests.
"""

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


def shuffled(text: str) -> str:
    values = list(text)
    random.shuffle(values)
    return ''.join(values)


class ScorerTests(unittest.TestCase):
    longMessage = True

    def construct_scorer(self, robot_contents, zone_tokens):
        return Scorer(
            {
                tla: {**info, 'robot_tokens': robot_contents.get(tla, "")}
                for tla, info in self.teams_data.items()
            },
            {x: {'tokens': y} for x, y in zone_tokens.items()},
        )

    def assertScores(self, expected_scores, robot_contents, zone_tokens):
        scorer = self.construct_scorer(robot_contents, zone_tokens)
        scorer.validate(None)
        actual_scores = scorer.calculate_scores()

        self.assertEqual(expected_scores, actual_scores, "Wrong scores")

    def assertInvalidScoresheet(self, robot_contents, zone_tokens, *, code):
        scorer = self.construct_scorer(robot_contents, zone_tokens)

        with self.assertRaises(InvalidScoresheetException) as cm:
            scorer.validate(None)

        self.assertEqual(
            code,
            cm.exception.code,
            f"Wrong error code, message was: {cm.exception}",
        )

    def setUp(self):
        self.teams_data = {
            'ABC': {'zone': 0, 'present': True, 'left_scoring_zone': False},
            'DEF': {'zone': 1, 'present': True, 'left_scoring_zone': False},
        }
        tokens_per_zone = 'B' * 5 + 'S' * 3 + 'G'
        self.zone_tokens = {
            0: shuffled(tokens_per_zone),
            1: shuffled(tokens_per_zone),
            2: shuffled(tokens_per_zone),
            3: shuffled(tokens_per_zone),
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

    ...

    # Invalid characters

    ...

    # Missing tokens

    ...

    # Extra tokens

    ...

    # Tolerable input deviances

    ...

    # Impossible scenarios

    ...


if __name__ == '__main__':
    unittest.main()
