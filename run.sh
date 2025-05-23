#!/bin/bash

cd $(dirname "${BASH_SOURCE[0]}")

uv run --module piscanner "$@"
