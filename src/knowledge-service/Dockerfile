FROM python:3.14-slim AS runtime

LABEL org.opencontainers.image.title="kamerplanter-knowledge-service" \
      org.opencontainers.image.description="RAG-based plant knowledge assistant for Kamerplanter" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --root-user-action=ignore -r requirements.txt

COPY app/ ./app/

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
