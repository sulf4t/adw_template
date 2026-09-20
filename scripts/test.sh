#!/bin/bash
# Run the kit's own tests. No Claude Code call: the agent runner is stubbed.
set -e
cd "$(dirname "$0")/.."
exec uv run --quiet --python '>=3.10' --with pytest --with pydantic --with python-dotenv --with click --with rich python -m pytest "$@"
