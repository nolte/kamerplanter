FROM busybox:1.38.0@sha256:fd8d9aa63ba2f0982b5304e1ee8d3b90a210bc1ffb5314d980eb6962f1a9715d

LABEL org.opencontainers.image.title="kamerplanter-knowledge" \
      org.opencontainers.image.description="Kamerplanter knowledge base init container" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

COPY spec/knowledge/rag/ /knowledge/

# Run as the non-root numeric "nobody" user. The copied knowledge files are
# world-readable; writing to the mounted /target emptyDir needs a matching
# fsGroup (or a runAsUser override) in the deployment.
USER 65534

# Init container entrypoint: copy knowledge files to shared volume.
# Mount an emptyDir at /target — all knowledge YAMLs are copied there.
ENTRYPOINT ["sh", "-c", "cp -r /knowledge/* /target/ && echo 'knowledge files copied'"]
