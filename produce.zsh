#!/bin/zsh
set -eu
project_dir=${0:A:h}
interpreter="$project_dir/.venv/bin/python"
if [[ ! -x "$interpreter" ]]; then
    interpreter="$project_dir/../.venv/bin/python"
fi
if [[ ! -x "$interpreter" ]]; then
    print -u2 "Create the local Python environment using README.md, then retry."
    exit 1
fi
exec "$interpreter" "$project_dir/Code/produce.py" "$@"
