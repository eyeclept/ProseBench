#!/usr/bin/env bash
set -euo pipefail
repo=$(realpath "$(dirname "${BASH_SOURCE[0]}")/..")
exec /home/eyeclept/Documents/School/DataMining-645/Project/.venv/bin/python "$repo/container/smoke.py"
