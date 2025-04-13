#!/bin/bash

set -euo pipefail

git pull srobo-score-entry main --ff-only && srcomp deploy . && git push && ssh srobo-score-entry 'cd compstate && git pull --ff-only' && git fetch srobo-score-entry
