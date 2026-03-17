FROM python:3.14-slim AS base

LABEL org.opencontainers.image.description="Kamerplanter backend API for plant lifecycle management"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl=7.* \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
