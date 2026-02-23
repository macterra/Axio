#!/usr/bin/env bash
cd "$(dirname "$0")"
qmd update 2>/dev/null
streamlit run axionagent/streamlit_app.py
