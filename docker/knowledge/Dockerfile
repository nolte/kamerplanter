FROM busybox:1.37.0

LABEL org.opencontainers.image.title="kamerplanter-knowledge" \
      org.opencontainers.image.description="Kamerplanter knowledge base init container" \
      org.opencontainers.image.source="https://github.com/nolte/kamerplanter" \
      org.opencontainers.image.vendor="Kamerplanter" \
      org.opencontainers.image.licenses="MIT"

COPY spec/knowledge/rag/ /knowledge/

# Init container entrypoint: copy knowledge files to shared volume.
# Mount an emptyDir at /target — all knowledge YAMLs are copied there.
ENTRYPOINT ["sh", "-c", "cp -r /knowledge/* /target/ && echo 'knowledge files copied'"]
