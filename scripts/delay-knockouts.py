#!/usr/bin/env python3
"""
Shift a static knockout schedule by a given timedelta.

Requires sr.comp.cli
"""
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from itertools import islice

from sr.comp.cli import yaml_round_trip as yaml
from sr.comp.cli.add_delay import parse_duration, parse_time

# import ruamel.yaml

# yaml = ruamel.yaml.YAML()  # defaults to round-trip if no parameters given
# yaml.Constructor.add_constructor(
#     'tag:yaml.org,2002:timestamp',
#     lambda _, node: datetime.fromisoformat(node.value),
# )

# def load_schedule(filename: Path):
#     """Load a schedule from a file."""
#     return yaml.load(filename.read_text())

# def save_schedule(filename: Path, schedule):
#     """Save a schedule to a file."""
#     yaml.dump(schedule, filename)


def shift_schedule(
    knockouts,
    shift: timedelta,
    starting_round: int,
    starting_match: int,
    slot_duration: int = 0,
    squash_slack: bool = False,
    round_spacing: int = 5 * 60,
):
    """Shift the schedule by a given timedelta."""

    round_gap = timedelta(seconds=round_spacing)
    slot_period = timedelta(seconds=slot_duration)
    last_start_time = knockouts[starting_round][starting_match]['start_time']

    # Shift the start time of the matches after the starting match in the starting round
    knockout = knockouts.get(starting_round, {})
    for idx, match in islice(knockout.items(), starting_match, None):
            spacing = match['start_time'] - last_start_time - slot_period
            last_start_time = match['start_time']
            print(f"Match {idx} spacing: {spacing}")
            if squash_slack:
                if idx == 0:  # Add round gap here
                    spacing -= round_gap

                # Remove additional spacing to make up the time
                if spacing > timedelta(0):
                    shift -= spacing

                if shift <= timedelta(0):
                    return

            match['start_time'] += shift

    # Shift the start time of all matches in the rounds after the starting round
    for knockout in islice(knockouts.values(), starting_round + 1, None):
        for idx, match in knockout.items():
            spacing = match['start_time'] - last_start_time - slot_period
            last_start_time = match['start_time']
            print(f"Match {idx} spacing: {spacing}")
            if squash_slack:
                if idx == 0:  # Add round gap here
                    spacing -= round_gap

                # Remove additional spacing to make up the time
                if spacing > timedelta(0):
                    shift -= spacing

                if shift <= timedelta(0):
                    return

            match['start_time'] += shift



def match_after_time(knockouts, target_time: datetime):
    """Find the first match after a given time."""
    for round_num, matches in knockouts.items():
        for match_num, match in matches.items():
            if match['start_time'] >= target_time:
                return round_num, match_num
    return None, None


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Shift a static knockout by a given timedelta.")
    parser.add_argument("compstate", type=Path, help="competition state repository")
    parser.add_argument(
        'how_long',
        help=(
            "How long to delay the knockouts for. Specify either as a number "
            "of seconds or as a string of the form 1m30s."
        ),
    )
    parser.add_argument(
        'when',
        nargs='?',
        default='now',
        help=(
            "When the delay should occur. This can be specified in a number of "
            "formats: an absolute time (parsed by dateutil), 'now', "
            "'current match' (the start of the current match slot), "
            "'<duration> ago' or 'in <duration>' where <duration> is specified "
            "as a number of seconds or a string of the form 1m30s. "
            "Assumes all times are in the current timezone, regardless of input."
        ),
    )
    parser.add_argument(
        "--absolute",
        action="store_true",
        help="Treat how_long as an absolute time in ISO format and shift the first selected match to that time",
    )
    parser.add_argument(
        "--squash-slack",
        action="store_true",
        help="Avoid moving all matches by removing the slack time between matches to make up the time",
    )
    parser.add_argument(
        "--round-spacing",
        type=int,
        default=5*60,
        help="Set the minimum time that will be maintained between matches.",
    )

    return parser.parse_args()


def main():
    """Main function to load and save a schedule."""
    args = parse_args()
    schedule_file = args.compstate / "schedule.yaml"
    schedule = yaml.load(schedule_file)

    if 'static_knockout' not in schedule:
        raise ValueError("No static knockout found in schedule")

    knockout = schedule['static_knockout']['matches']

    when = parse_time(args.compstate, args.when)
    when = when.replace(microsecond=0)

    round_num, match_num = match_after_time(knockout, when)
    if round_num is None:
        raise ValueError("No match found after the specified time")

    if args.absolute:
        new_time = parse_time(args.compstate, args.how_long)
        current_time = knockout[round_num][match_num]['start_time']
        how_long = new_time - current_time
    else:
        how_long = parse_duration(args.how_long)

    slot_duration = schedule['match_slot_lengths']['total']

    shift_schedule(knockout, how_long, round_num, match_num, slot_duration, args.squash_slack, args.round_spacing)

    # Save the updated schedule
    yaml.dump(schedule, dest=schedule_file)

    print(f"Shifted schedule by {how_long} from {when} to {when + how_long}")


if __name__ == "__main__":
    main()
