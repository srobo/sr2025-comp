#!/usr/bin/env python3

"""
Prepare content for feeding to virtual competition livestream commentators.

Usage:

1. Run this script for the relevant virtual competition matches, directing the
   output to an HTML file -- perhaps like:

    ./livestream-helper.py 0-9 > livestream-doc.html

2. Open that file in a browser.
3. Copy the content of the rendered file into the commentator doc.

During matches, sections of the doc between the horizontal rules will be copied
into Slack to tell the commentators about the past match result and the teams in
the next match.
"""

import argparse
import logging
import statistics
import sys
from collections.abc import Iterable
from pathlib import Path

from sr.comp.comp import SRComp
from sr.comp.match_period import Match
from sr.comp.matches import parse_ranges
from sr.comp.types import TLA, MatchNumber

ZONE_COLOUR_MAP = dict(enumerate([
    'large_green_square',
    'large_orange_square',
    'large_purple_square',
    'large_yellow_square',
]))

ORDINALS = {
    1: "1st",
    2: "2nd",
    3: "3rd",
    4: "4th",
}

logging.basicConfig(stream=sys.stderr)


def get_matches(comp: SRComp, numbers: Iterable[MatchNumber]) -> Iterable[Match]:
    for num in numbers:
        slot = comp.schedule.matches[num]
        yield from slot.values()


def team_mean_game_points(
    comp: SRComp,
    matches: Iterable[Match],
    team: TLA,
) -> float:
    return statistics.mean(
        score.game[team]
        for match in matches
        if (score := comp.scores.get_scores(match)) is not None
    )


def main(match_numbers: set[MatchNumber], compstate_dir: Path) -> None:
    comp = SRComp(compstate_dir)

    matches = list(get_matches(comp, sorted(match_numbers)))

    for match in matches:
        team_zone_map = dict(zip(match.teams, ZONE_COLOUR_MAP.items()))
        past_matches = [m for m in matches if m.num < match.num]

        print('<br>')
        print('<span style="white-space: pre">', end='')
        print(f"<strong>{match.display_name}:</strong>")
        for team, (zone_id, colour) in team_zone_map.items():
            print(f":{colour}: Zone {zone_id} 	{team} 	TEAM-COMMENT-HERE", end='')
            # TODO: annotate first & final appearances
            if team and past_matches:
                mean_game_points = team_mean_game_points(
                    comp,
                    past_matches,
                    team,
                )
                print(f". Mean game points: {mean_game_points}")
            else:
                print()
        print('</span>')

        print('<br>')
        print(f"<strong>{match.display_name} Analysis:</strong>")
        print('<ul style="margin: 0"><li>ANALYSIS HERE</li></ul>')
        print()
        print('<hr>')

        scores = comp.scores.get_scores(match)
        if not scores:
            logging.warning(f"Missing scores for {match.display_name}")
            continue

        print('<br>')
        print('<span style="white-space: pre">', end='')
        print(f"<strong>{match.display_name} Results:</strong>")
        for team, rank in scores.ranking.items():
            zone_id, colour = team_zone_map[team]
            print(
                f"{ORDINALS[rank]}   	:{colour}: {team} - Zone {zone_id} 	{scores.game[team]} points",
            )
        print('</span>')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        metavar='match-numbers',
        dest='match_numbers',
        type=parse_ranges,
        help="Matches to show. Accepts comma separated values or hyphenated ranges: 1,3-5.",
    )
    parser.add_argument(
        metavar='compstate',
        dest='compstate_dir',
        nargs=argparse.OPTIONAL,
        default=Path(__file__).parent,
        type=Path,
    )
    return parser.parse_args()


if __name__ == '__main__':
    main(**parse_args().__dict__)
