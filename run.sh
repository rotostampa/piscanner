#!/bin/bash

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
uv run --with "file://${SCRIPT_DIR}" --module piscanner "$@"
