#!/usr/bin/env bash
set -e
# Stub build script for Render
# If a real build is needed, replace with actual steps.
if [ -f ./scripts/render_build.sh ]; then
  ./scripts/render_build.sh "$@"
  exit $?
fi
echo 'render_build.sh: no-op (edge agent repo)'