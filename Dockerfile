FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY knowledge ./knowledge
COPY schemas ./schemas
COPY core.py main.py app.py formsiq-logo.png ./
COPY .streamlit ./.streamlit

EXPOSE 8000 8501

# Default: API (compose overrides for UI)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
