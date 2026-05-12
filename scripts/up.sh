#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  if [[ -f .env.example ]]; then
    cp .env.example .env
    echo "Created .env from .env.example — set GEMINI_API_KEY"
  else
    echo "Create .env with GEMINI_API_KEY=" >&2
  fi
fi

docker compose -p formsiq up --build "$@"
