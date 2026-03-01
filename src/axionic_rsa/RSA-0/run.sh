#!/usr/bin/env bash
source ~/Axio/.venv/bin/activate
cd "$(dirname "$0")"
qmd update 2>/dev/null
streamlit run axionagent/streamlit_app.py
