#!/usr/bin/env bash
source ~/Axio/.venv/bin/activate
cd "$(dirname "$0")"
python -m axionagent.slack_app
