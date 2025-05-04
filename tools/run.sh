#!/usr/bin/env bash
cd "$(dirname "$0")/.."
if [ ! -d venv ]; then
  python -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
else
  source venv/bin/activate
fi
uvicorn app.main:app --host 127.0.0.1 --port 8000
