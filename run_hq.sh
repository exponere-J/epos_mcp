#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
export PYTHONPATH="$PWD"
streamlit run epos_hq/ui/command_center.py
