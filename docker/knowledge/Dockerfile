FROM busybox:1.38.0@sha256:fd7dc98638c8e305f4dc34e979f1c0fdfdcaeb0fbf8fcff77ae834b6da3d7e6e

LABEL org.opencontainers.image.title="kamerplanter-knowledge" \
      org.opencontainers.image.description="Init container that seeds Kamerplanter's RAG knowledge-base YAML files into a shared volume for the vector store" \
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
