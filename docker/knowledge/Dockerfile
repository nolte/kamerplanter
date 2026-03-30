FROM busybox:1.37.0

COPY spec/knowledge/ /knowledge/

# Init container entrypoint: copy knowledge files to shared volume.
# Mount an emptyDir at /target — all knowledge YAMLs are copied there.
ENTRYPOINT ["sh", "-c", "cp -r /knowledge/* /target/ && echo 'knowledge files copied'"]
