FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --no-cache-dir .

EXPOSE 8000

# Runs fully offline: the bundled synthetic corpora are the default data source.
CMD ["uvicorn", "research_system.api:app", "--host", "0.0.0.0", "--port", "8000"]
