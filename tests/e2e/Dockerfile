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

# Run as a non-root numeric user. A mounted report/screenshot volume needs
# a matching fsGroup:1000 in the deployment to stay writable.
RUN groupadd -g 1000 app && useradd -u 1000 -g 1000 -d /app -s /usr/sbin/nologin app \
    && chown -R 1000:1000 /app
USER 1000

ENTRYPOINT ["pytest", "--tb=short", "--generate-protocol"]
