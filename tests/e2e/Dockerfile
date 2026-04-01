FROM python:3.14-slim

LABEL org.opencontainers.image.title="kamerplanter-e2e-tests" \
      org.opencontainers.image.description="Kamerplanter Selenium E2E test runner" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["pytest", "--tb=short", "--generate-protocol"]
