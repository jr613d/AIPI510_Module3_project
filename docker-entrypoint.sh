#!/bin/sh
# Container entry points: serve (default), train, test.
# Extra arguments are passed through, e.g. `train --tracking-mode disabled`.
set -e

command="${1:-serve}"
[ "$#" -gt 0 ] && shift

case "$command" in
  serve)
    echo "Serving model $(cat MODEL_SHA256) on port ${PORT}"
    exec python -m src.api --host 0.0.0.0 --port "${PORT}" "$@"
    ;;
  train)
    exec python -m src.train "$@"
    ;;
  test)
    exec python -m unittest discover -s tests "$@"
    ;;
  *)
    echo "Unknown command '$command'. Use: serve | train | test" >&2
    exit 2
    ;;
esac
