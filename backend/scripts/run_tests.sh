#!/usr/bin/env bash
set -euo pipefail

export PYTHONPATH=.
pytest -q tests
