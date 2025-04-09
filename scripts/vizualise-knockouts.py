#!/usr/bin/env python3

# See https://stackoverflow.com/a/10802842

import subprocess
import textwrap
from pathlib import Path

import yaml
from sr.comp.knockout_scheduler.static_scheduler import StaticMatchInfo

COMPSTATE_DIR = Path(__file__).parent


def match_id(round_num: int, match_num: int) -> str:
    return f'R{round_num}M{match_num}'


def match_as_dot(match_id: str, info: StaticMatchInfo) -> str:
    produces_teams = ' '.join(
        f'{match_id}P{x}' for x in range(len(info['teams']))
    )

    title = info['display_name']
    return '\n'.join((
        f'subgraph cluster_match_{match_id} {{',
        f'    label = "{title}"',
        f'    {match_id}_node [shape=point style=invis]',
        f'    {produces_teams}',
        '}',
    ))


def teams_as_dot(match_id: str, info: StaticMatchInfo) -> str:
    competing_teams = '; '.join(
        'R{}M{}P{}'.format(*x) if x.isdecimal() and len(x) == 3 else x
        for x in info['teams']
        if x is not None
    )
    return f'{{ {competing_teams} }} -> {match_id}_node [lhead=cluster_match_{match_id}]'


def round_as_dot(round_num: int, matches: dict[int, StaticMatchInfo]) -> str:
    matches_body = textwrap.indent(
        '\n' + '\n'.join(
            match_as_dot(match_id(round_num, match_num), info)
            for match_num, info in matches.items()
        ),
        '    ',
    )
    teams_body = textwrap.indent(
        '\n'.join(
            teams_as_dot(match_id(round_num, match_num), info)
            for match_num, info in matches.items()
        ),
        '    ',
    )

    round_id = f'cluster_round_{round_num}'
    return '\n'.join((
        f'subgraph {round_id} {{',
        matches_body,
        teams_body,
        '}',
    ))


def main():
    with (COMPSTATE_DIR / 'schedule.yaml').open() as f:
        data = yaml.safe_load(f)
        static_knockout = data['static_knockout']

    body = '\n'.join(
        round_as_dot(round_num, info)
        for round_num, info in static_knockout['matches'].items()
    )
    graph = f'digraph {{ compound=true; {body} }}'

    with open('out.dot', mode='w') as f:
        print(graph, file=f)

    with open('out.pdf', mode='wb') as f:
        subprocess.run(
            ['dot', '-Grankdir=LR', '-Tpdf'],
            input=graph.encode(),
            stdout=f,
            check=True,
        )


if __name__ == '__main__':
    main()
