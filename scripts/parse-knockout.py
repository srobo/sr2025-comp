#!/usr/bin/env python3

import argparse
import collections
import csv
import datetime
import re

import dateutil.tz
import yaml

TZ = dateutil.tz.gettz('Europe/London')

OFFSET = 10


parser = argparse.ArgumentParser()
parser.add_argument('--verbose', action='store_true')
parser.add_argument('knockouts_csv', type=argparse.FileType('r'))
parser.add_argument('--output', required=True, type=argparse.FileType('w'))
args = parser.parse_args()

rows = list(csv.reader(args.knockouts_csv))

starts = []
for row_idx, row in enumerate(rows[OFFSET:], start=OFFSET):
    for cell_idx, cell in enumerate(row):
        if cell.isdigit() and len(cell) == 3 and not row[cell_idx + 1]:
            starts.append(
                (row_idx, cell_idx),
            )

raw_matches = {}


def get_id(start):
    row_idx, cell_idx = start
    return rows[row_idx][cell_idx]


def get_ref(start):
    row_idx, cell_idx = start
    return rows[row_idx + 2][cell_idx]


def get_time(start):
    row_idx, cell_idx = start
    return rows[row_idx + 1][cell_idx]


def parse_team(row_idx, cell_idx):
    text = rows[row_idx][cell_idx]

    if (match := re.match(r'P(\d+) in League', text)) is not None:
        seed_num = match.group(1)
        return lambda: f"S{seed_num}"

    if (match := re.match(r'P(\d+) in #(\d{3})', text)) is not None:
        def lookup():
            pos = int(match.group(1)) - 1
            match_id = match.group(2)

            raw_match = raw_matches[match_id]
            ref = raw_match['ref']
            if len(ref) > 2:
                round_num = ref[:-1]
                match_num = ref[-1]
                prefix = f'R{round_num}M{match_num}P'
            else:
                prefix = ref

            return prefix + str(pos)

        return lookup

    raise AssertionError(f"Failed to parse {text!r} from {row_idx}, {cell_idx}!")


def get_teams(start):
    row_idx, cell_idx = start
    row_idx += 1
    cell_idx += 1
    return [
        parse_team(row_idx, cell_idx),
        parse_team(row_idx, cell_idx + 1),
        parse_team(row_idx + 1, cell_idx + 1),
        parse_team(row_idx + 1, cell_idx),
    ]


def parse_match(start):
    if args.verbose:
        print(f"Parsing match at {start}: #{get_id(start)}")
    return {
        'id': get_id(start),
        'ref': get_ref(start),
        'start_time': get_time(start),
        'teams': get_teams(start),
    }


for start in starts:
    raw_match = parse_match(start)
    raw_matches[raw_match['id']] = raw_match


rounds = collections.defaultdict(dict)
for _, raw_match in sorted(raw_matches.items()):
    if args.verbose:
        print(f"Processing raw match #{raw_match['id']}")

    ref = raw_match['ref']
    if ref:
        round_num = int(ref[:-1])
        match_num = int(ref[-1])
    else:
        round_num = len(rounds)
        match_num = 0

    hour, minute = (int(x) for x in raw_match['start_time'].split(':'))

    rounds[round_num][match_num] = {
        'arena': 'main',
        'start_time': datetime.datetime(2025, 4, 13, hour, minute, tzinfo=TZ),
        'teams': [x() for x in raw_match['teams']],
    }


yaml.safe_dump(
    {
        'static_knockout': {
            'teams_per_arena': 4,
            'matches': dict(rounds),
        },
    },
    args.output,
)
