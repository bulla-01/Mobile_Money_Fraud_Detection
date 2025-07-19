#!/bin/sh
/app/wait-for-it.sh db:5432 -- uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}
