.PHONY: up down test eval api ui

# Docker: full stack (API + Streamlit)
up:
	docker compose -p formsiq up --build

down:
	docker compose -p formsiq down

# Local API (requires .env with GEMINI_API_KEY)
api:
	uvicorn main:app --reload --host 127.0.0.1 --port 8000

ui:
	streamlit run app.py

test:
	PYTHONPATH=. $(PYTHON) tests/test_core.py

eval:
	PYTHONPATH=. $(PYTHON) eval/run_eval.py

# Override on Windows if needed: make PYTHON=python test
PYTHON ?= python3
