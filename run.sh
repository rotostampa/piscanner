#!/bin/bash

cd $(dirname "${BASH_SOURCE[0]}")

uv venv
uv pip install .
.venv/bin/python -m piscanner "$@"
