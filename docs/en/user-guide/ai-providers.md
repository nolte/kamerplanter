# AI Provider Setup

!!! info "Provider configuration happens via operator environment variables, not the interface"
    There is no "Settings > AI Provider" screen in the Kamerplanter interface. The AI provider is configured exclusively through **environment variables on the Knowledge Service** (`src/knowledge-service/app/config.py`). This is an operator task, not a user setting. Set the variables via Helm values, a `.env` file, or a Kubernetes secret. This page explains the setup for self-hosters and platform operators. The Ollama installation instructions and hardware recommendations below remain unchanged.

Kamerplanter supports multiple AI providers that can be chosen based on hardware, privacy requirements, and budget. This page explains how to set up each provider and configure it on the Knowledge Service.

---

## Prerequisites

- Kamerplanter (including the Knowledge Service) is deployed
- Access to the Knowledge Service's environment variable configuration (Helm `values.yaml`, `.env` file, or Kubernetes secret) — operator role

---

## Overview of the Relevant Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | `anthropic`, `ollama`, or `openai_compatible` | `ollama` |
| `LLM_API_URL` | Base URL of the provider (for Ollama/OpenAI-compatible) | `http://ollama:11434` |
| `LLM_API_KEY` | API key (for Anthropic/OpenAI-compatible, if required) | empty |
| `LLM_MODEL` | Model name | `gemma3:12b` |
| `LLM_MAX_TOKENS` | Maximum response length | `2048` |
| `LLM_TEMPERATURE` | Response creativity (0.0–1.0) | `0.1` |

!!! warning "RAM note for the default model"
    The default `gemma3:12b` needs significantly more RAM/VRAM than smaller models (see the hardware table below). On smaller hardware, set `LLM_MODEL` explicitly to a suitable model (e.g. `llama3.2:3b` or `gemma3:4b`).

## Provider Overview

| Provider | Type | Privacy | Cost | Recommendation |
|----------|------|---------|------|----------------|
| [Ollama](#ollama-local-recommended) | Local | No data sharing | Free | Self-hosted |
| [llama.cpp HTTP Server](#llamacpp-http-server) | Local | No data sharing | Free | Advanced users |
| [OpenAI API](#openai-api) | Cloud | Transferred to OpenAI (USA) | Pay-per-token | Best quality |
| [Anthropic Claude API](#anthropic-claude-api) | Cloud | Transferred to Anthropic (USA) | Pay-per-token | Best quality |
| [OpenAI-compatible APIs](#openai-compatible-apis) | Local or Cloud | Depends | Variable | Advanced users |

!!! tip "Recommendation for getting started"
    If self-hosting: start with **Ollama + gemma3:4b**. This model runs on most desktop computers from 2020 onwards without a GPU and shares no data externally.

---

## Ollama (Local, Recommended)

Ollama is a program that runs language models locally on a machine or server. No data leaves the network.

### Hardware Requirements

| Hardware | RAM | Recommended Model | Response Time (Tip Cards) |
|----------|-----|--------------------|--------------------------|
| Raspberry Pi 5, older NUCs | 8 GB | `llama3.2:3b` | 15–30 seconds |
| Desktop/laptop from 2020+ | 16 GB | `gemma3:4b` | 10–20 seconds |
| GPU 6–8 GB VRAM (GTX 1060, RX 580) | — | `mistral:7b` | 2–5 seconds |
| GPU 12 GB VRAM (RTX 3060) | — | `llama3.1:8b` | 1–3 seconds |
| GPU 16 GB VRAM and more | — | `mistral-small:22b` | 2–5 seconds |

!!! note "Why small models work well"
    Kamerplanter sends a precise context (current phase, EC/pH/VPD, care history) directly to the model. A 4B model with concrete context produces better plant tips than a 70B model without context.

### Installing Ollama

=== "Linux"

    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ```

    The Ollama service starts automatically and is available at `http://localhost:11434`.

=== "macOS"

    Download the installer from [ollama.com/download](https://ollama.com/download) and open the `.dmg` file.

    After installation, the Ollama icon appears in the menu bar.

=== "Windows"

    Download the installer from [ollama.com/download](https://ollama.com/download) and run it.

    Ollama runs as a background service and is available at `http://localhost:11434`.

=== "Docker"

    ```bash
    docker run -d --name ollama \
      -p 11434:11434 \
      -v ollama_data:/root/.ollama \
      ollama/ollama
    ```

    With GPU support (NVIDIA):

    ```bash
    docker run -d --name ollama \
      --gpus all \
      -p 11434:11434 \
      -v ollama_data:/root/.ollama \
      ollama/ollama
    ```

### Downloading a Model

Open a terminal and download the recommended model:

```bash
# Recommended for most users (16 GB RAM)
ollama pull gemma3:4b

# For machines with less RAM (8 GB)
ollama pull llama3.2:3b

# For GPU users with 8+ GB VRAM
ollama pull mistral:7b
```

!!! tip "Test Ollama"
    Verify that Ollama works:
    ```bash
    ollama run gemma3:4b "What temperature does basil need during germination?"
    ```

### Configuring on the Knowledge Service

Set the following environment variables for the Knowledge Service (e.g. in the Helm values or the `.env` file) and restart the service:

```bash
LLM_PROVIDER=ollama
LLM_API_URL=http://ollama:11434   # or the IP/service name of the Ollama host
LLM_MODEL=gemma3:4b
```

!!! warning "Ollama on another host"
    If Ollama runs on a different machine (e.g. a NAS), `LLM_API_URL` must point to that machine's IP address or DNS name. Port 11434 must be reachable from the Knowledge Service's network.

---

## llama.cpp HTTP Server

llama.cpp is an alternative to Ollama for advanced users who want to use GGUF models directly from the Hugging Face community or other sources.

### Starting the Server

```bash
# llama.cpp HTTP server (after compilation)
./llama-server \
  --model /path/to/model.gguf \
  --host 0.0.0.0 \
  --port 8080 \
  --ctx-size 4096
```

### Configuring on the Knowledge Service

llama.cpp offers an OpenAI-compatible API, so the `openai_compatible` provider is used:

```bash
LLM_PROVIDER=openai_compatible
LLM_API_URL=http://localhost:8080   # base URL WITHOUT /v1 — the adapter appends /v1/chat/completions itself
LLM_API_KEY=                        # leave empty
LLM_MODEL=local                     # or the name of the loaded GGUF model
```

---

## OpenAI API

OpenAI provides high-quality cloud models. Plant data is transferred to OpenAI servers in the USA for every request.

!!! warning "Privacy notice"
    When using the OpenAI API, plant data (phase, measurements, cultivar name, fertilization history) is transferred to OpenAI in the USA. The operator is responsible for disclosing this in the instance's privacy notice.

### Creating an API Key

1. Open [platform.openai.com](https://platform.openai.com)
2. Sign in (or create an account)
3. Navigate to **API keys**
4. Click **Create new secret key**
5. Copy the key (it is only shown once)

### Configuring on the Knowledge Service

There is no dedicated `openai` provider value — OpenAI is reached through `openai_compatible` with OpenAI's base URL:

```bash
LLM_PROVIDER=openai_compatible
LLM_API_URL=https://api.openai.com   # base URL WITHOUT /v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

### Recommended Models

| Model | Strengths | Approximate Cost |
|-------|-----------|-----------------|
| `gpt-4o-mini` | Fast, affordable, good for simple diagnoses | ~$0.001 per request |
| `gpt-4o` | Best quality, complex reasoning | ~$0.01 per request |

---

## Anthropic Claude API

Anthropic Claude is an alternative to OpenAI with strong analytical capabilities. Data is also transferred to servers in the USA.

!!! warning "Privacy notice"
    Analogous to the OpenAI API: plant data is transferred to Anthropic servers in the USA for every request. The operator is responsible for disclosing this in the privacy notice.

### Creating an API Key

1. Open [console.anthropic.com](https://console.anthropic.com)
2. Sign in (or create an account)
3. Navigate to **API Keys**
4. Click **Create Key**
5. Copy the key

### Configuring on the Knowledge Service

```bash
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-...
LLM_MODEL=claude-sonnet-4-20250514   # adapter default if LLM_MODEL is not set
```

### Recommended Models

| Model | Strengths | Approximate Cost |
|-------|-----------|-----------------|
| `claude-haiku-4-5` | Very fast, affordable | ~$0.001 per request |
| `claude-sonnet-4-6` | Precise diagnoses, nuanced responses | ~$0.008 per request |

---

## OpenAI-Compatible APIs

Many local and cloud services offer an OpenAI-compatible API. These include:

- **LM Studio** — GUI application for local models (Windows/macOS/Linux)
- **vLLM** — High-performance inference for servers
- **Together AI** — Cloud service with open-source models
- **Mistral AI** — Cloud service with Mistral models
- **Groq** — Very fast cloud inference

### Configuring on the Knowledge Service

```bash
LLM_PROVIDER=openai_compatible
LLM_API_URL=<base URL of the service without /v1>   # e.g. http://localhost:1234 for LM Studio
LLM_API_KEY=<if required, otherwise empty>
LLM_MODEL=<model name>
```

!!! example "LM Studio example"
    LM Studio starts a local server at `http://localhost:1234`.
    `LLM_API_URL=http://localhost:1234`, `LLM_MODEL=lmstudio-community/gemma-3-4b-it-GGUF`.

---

## Provider Priority and Fallback

The Knowledge Service currently uses **exactly one** configured provider (`LLM_PROVIDER`) — there is no multi-provider configuration with automatic failover between several cloud/local providers.

If no provider is reachable or `POST /api/v1/knowledge/ask` fails, the **rule-based fallback** for tip cards applies once that feature is available: the system generates tip cards based on master data and the current phase — without a language model.

---

## Frequently Asked Questions

??? question "Can I use different providers for different features?"
    No, the Knowledge Service currently uses the single configured provider (`LLM_PROVIDER`) for all AI features. Per-feature provider selection is not supported.

??? question "How can I control cloud provider usage costs?"
    OpenAI and Anthropic provide usage dashboards and budget limits in their control panels.

??? question "Ollama won't start or is unreachable — what should I do?"
    Check: (1) Is the Ollama service running? (`systemctl status ollama` on Linux). (2) Is Ollama on port 11434? (`curl http://localhost:11434`). (3) Is the model downloaded? (`ollama list`). (4) Does `LLM_API_URL` point to the correct host?

??? question "The model responds in a different language — what can I do?"
    By default, the Knowledge Service sends all requests in German (`RAG_PROMPT_LANGUAGE=de`). Model behavior also depends on the model itself. If a model still consistently responds in English, a larger model helps (`gemma3:4b` instead of `llama3.2:3b`). English-speaking self-hosters can set `RAG_PROMPT_LANGUAGE=en` to change the default prompt language.

---

## See Also

- [AI Assistant](ai-assistant.md)
- [Understanding the RAG Knowledge Base](../guides/rag-knowledge-base.md)
- [Environment Variables](../reference/environment-variables.md)
