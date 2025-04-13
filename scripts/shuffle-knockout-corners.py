import random
from sr.comp.cli import yaml_round_trip as yaml

with open('schedule.yaml') as f:
    sched = yaml.load(f)

for round_ in sched['static_knockout']['matches'].values():
    for match in round_.values():
        print(match['teams'])

for round_ in sched['static_knockout']['matches'].values():
    for match in round_.values():
        random.shuffle(match['teams'])

for round_ in sched['static_knockout']['matches'].values():
    for match in round_.values():
        print(match['teams'])

with open('schedule.yaml', mode='w') as f:
    sched = yaml.dump(sched, dest=f)
