#!/usr/bin/env bash
# Build the site (scripts/build.sh -- the same script CI runs) and serve _site/
# locally, so a local preview is byte-for-byte what CI deploys.
#
# Usage: bash scripts/serve.sh [port]   (default port 8000)
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
port="${1:-8000}"

bash scripts/build.sh

# Pick a Python that actually runs (on Windows `python3` is often a Microsoft
# Store stub that isn't real Python), preferring python3 on Unix.
py=""
for c in python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c "import sys" >/dev/null 2>&1; then
    py="$c"; break
  fi
done
[ -n "$py" ] || { echo "error: no working python found" >&2; exit 1; }

echo "Serving _site/ at http://localhost:$port/  (Ctrl-C to stop)"
exec "$py" -m http.server "$port" --directory _site
