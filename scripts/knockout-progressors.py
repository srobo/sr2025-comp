#!/usr/bin/env python3

import argparse
import collections
import itertools
from pathlib import Path
from typing import IO, Text

import yaml
from sr.comp.knockout_scheduler.static_scheduler import (
    StaticMatchInfo,
    StaticMatchTeamReference,
    parse_team_ref,
)

COMPSTATE_DIR = Path(__file__).parent


def lookup_result(
    results: dict[tuple[int, int], list[StaticMatchTeamReference | None]],
    team_ref: StaticMatchTeamReference | None,
) -> StaticMatchTeamReference | None:
    if team_ref is None:
        return None

    if team_ref.startswith('S'):
        return team_ref

    round_num, match_num, position = parse_team_ref(team_ref)

    return results[round_num, match_num][position]


def seed_key(seed_ref: str | None) -> float:
    if seed_ref is None:
        return float('inf')

    assert seed_ref.startswith('S')
    return int(seed_ref[1:])


def main(schedule_yaml: IO[Text]) -> None:
    data = yaml.safe_load(schedule_yaml)
    static_knockout = data['static_knockout']

    results: dict[tuple[int, int], list[StaticMatchTeamReference | None]] = {}

    for round_num, round_info in static_knockout['matches'].items():
        match_info: StaticMatchInfo
        for match_num, match_info in round_info.items():
            match_id = (round_num, match_num)
            results[match_id] = sorted(
                (
                    lookup_result(results, x)
                    for x in match_info['teams']
                ),
                key=seed_key,
            )

    print("## Seeded appearances in matches:")
    print()
    for match_id, teams in sorted(results.items()):
        print(match_id, teams)
    print()

    print("## Seeded appearance counts:")
    print()
    appearances = collections.Counter(itertools.chain(*results.values()))
    for team, count in sorted(
        appearances.most_common(),
        key=lambda x: (x[1], seed_key(x[0])),
    ):
        print(team, count)
    print()

    print("## Seeds last appearances:")
    print()
    last_appearance = {}
    for match_id, teams in sorted(results.items()):
        for team in teams:
            last_appearance[team] = match_id

    for team, match_id in sorted(
        last_appearance.items(),
        key=lambda x: seed_key(x[0]),
    ):
        print(team, match_id)
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('schedule_yaml', type=argparse.FileType('r'))
    return parser.parse_args()


if __name__ == '__main__':
    main(**parse_args().__dict__)
