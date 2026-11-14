#!/usr/bin/env bash
# A throwaway local web server for the fixture site, used by the media specs.
#   serve.sh start DIR [PORT]   serve DIR on 127.0.0.1 (default port 8765), replacing any server started here
#   serve.sh stop               stop it
# The process id is kept in ./.serve.pid, so run both commands from the same folder.
set -eu
case "${1:-}" in
  start)
    "$0" stop
    python3 -m http.server "${3:-8765}" --bind 127.0.0.1 --directory "$2" >/dev/null 2>&1 &
    echo $! > .serve.pid
    sleep 0.7
    if ! kill -0 "$(cat .serve.pid)" 2>/dev/null; then
      rm -f .serve.pid
      echo "serve.sh: the server did not start (is port ${3:-8765} already in use?)" >&2
      exit 1
    fi
    ;;
  stop)
    if [ -f .serve.pid ]; then
      kill "$(cat .serve.pid)" 2>/dev/null || true
      rm -f .serve.pid
      sleep 0.3
    fi
    ;;
  *)
    echo "usage: serve.sh start DIR [PORT] | stop" >&2
    exit 2
    ;;
esac
