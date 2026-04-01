# Knowledge Init Container

Minimal BusyBox init container that copies the Kamerplanter knowledge base YAML files into a shared Kubernetes volume.

## Purpose

In a Kubernetes deployment the knowledge files from `spec/knowledge/` need to be available to the backend for RAG (Retrieval-Augmented Generation). This init container packages the files and copies them to an `emptyDir` volume at startup.

## How It Works

1. At build time, `spec/knowledge/` is copied into the image.
2. At runtime, the entrypoint copies all files to `/target/`.
3. A shared `emptyDir` volume mounted at `/target/` makes the files available to other containers in the pod.

## Build Context

The `.dockerignore` restricts the build context to `spec/knowledge/` only. The Dockerfile must be built from the repository root:

```bash
docker build -f docker/knowledge/Dockerfile -t kamerplanter-knowledge .
```

## Stack

- BusyBox 1.37.0
