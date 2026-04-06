# AI Provider Setup

Kamerplanter supports multiple AI providers that you can choose based on your hardware, privacy requirements, and budget. This page explains how to set up each provider and configure it in Kamerplanter.

---

## Prerequisites

- Kamerplanter is installed and running
- Access to **Settings > AI Provider** (tenant admin or own settings)

---

## Provider Overview

| Provider | Type | Privacy | Cost | Recommendation |
|----------|------|---------|------|----------------|
| [Ollama](#ollama-local-recommended) | Local | No data sharing | Free | Self-hosted |
| [llama.cpp HTTP Server](#llamacpp-http-server) | Local | No data sharing | Free | Advanced users |
| [OpenAI API](#openai-api) | Cloud | Transferred to OpenAI (USA) | Pay-per-token | Best quality |
| [Anthropic Claude API](#anthropic-claude-api) | Cloud | Transferred to Anthropic (USA) | Pay-per-token | Best quality |
| [OpenAI-compatible APIs](#openai-compatible-apis) | Local or Cloud | Depends | Variable | Advanced users |

!!! tip "Recommendation for getting started"
    If you self-host Kamerplanter: start with **Ollama + gemma3:4b**. This model runs on most desktop computers from 2020 onwards without a GPU and shares no data externally.

---

## Ollama (Local, Recommended)

Ollama is a program that runs language models locally on your machine or server. No data leaves your network.

### Hardware Requirements

| Hardware | RAM | Recommended Model | Response Time (Tip Cards) |
|----------|-----|-------------------|--------------------------|
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

### Configuring in Kamerplanter

1. Open **Settings > AI Provider**
2. Click **Add Provider**
3. Select **Ollama**
4. Enter the URL: `http://localhost:11434` (or your server's IP address)
5. Select the model from the dropdown (or type `gemma3:4b`)
6. Click **Save**, then **Test Connection**

!!! warning "Ollama on another machine"
    If Ollama runs on a different machine (e.g., a NAS), replace `localhost` with that machine's IP address. Ensure port 11434 is reachable on your network.

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

### Configuring in Kamerplanter

1. Open **Settings > AI Provider**
2. Click **Add Provider**
3. Select **OpenAI-compatible** (llama.cpp offers an OpenAI-compatible API)
4. Enter the URL: `http://localhost:8080`
5. Leave the API key field empty
6. Enter the model name as `local` or the name of your GGUF model
7. Click **Test Connection**

---

## OpenAI API

OpenAI provides high-quality cloud models. Your plant data is transferred to OpenAI servers in the USA for every request.

!!! warning "Privacy notice"
    When using the OpenAI API, your plant data (phase, measurements, cultivar name, fertilization history) is transferred to OpenAI in the USA. When using a cloud provider for the first time, Kamerplanter asks for your GDPR consent. You can revoke this at any time under **Settings > Privacy**.

### Creating an API Key

1. Open [platform.openai.com](https://platform.openai.com)
2. Sign in (or create an account)
3. Navigate to **API keys**
4. Click **Create new secret key**
5. Copy the key (it is only shown once)

### Configuring in Kamerplanter

1. Open **Settings > AI Provider**
2. Click **Add Provider**
3. Select **OpenAI**
4. Paste your API key
5. Choose a model:
   - **gpt-4o-mini** — affordable, fast, good for tip cards
   - **gpt-4o** — best quality, higher cost
6. Click **Save**

### Recommended Models

| Model | Strengths | Approximate Cost |
|-------|-----------|-----------------|
| `gpt-4o-mini` | Fast, affordable, good for simple diagnoses | ~$0.001 per request |
| `gpt-4o` | Best quality, complex reasoning | ~$0.01 per request |

---

## Anthropic Claude API

Anthropic Claude is an alternative to OpenAI with strong analytical capabilities. Data is also transferred to servers in the USA.

!!! warning "Privacy notice"
    Analogous to the OpenAI API: your plant data is transferred to Anthropic servers in the USA for every request. GDPR consent is required.

### Creating an API Key

1. Open [console.anthropic.com](https://console.anthropic.com)
2. Sign in (or create an account)
3. Navigate to **API Keys**
4. Click **Create Key**
5. Copy the key

### Configuring in Kamerplanter

1. Open **Settings > AI Provider**
2. Click **Add Provider**
3. Select **Anthropic**
4. Paste your API key
5. Choose a model:
   - **claude-haiku-4-5** — fast, affordable, good for tip cards
   - **claude-sonnet-4-6** — very good analysis quality
6. Click **Save**

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

### Configuring in Kamerplanter

1. Open **Settings > AI Provider**
2. Click **Add Provider**
3. Select **OpenAI-compatible**
4. Enter the **Base URL** of the service (e.g., `http://localhost:1234/v1` for LM Studio)
5. Enter an **API key** if the service requires one (leave empty for local services)
6. Enter the **model name**
7. Click **Test Connection**

!!! example "LM Studio example"
    LM Studio starts a local server at `http://localhost:1234/v1`.
    Model name: the name of the loaded model, e.g., `lmstudio-community/gemma-3-4b-it-GGUF`.

---

## Provider Priority and Fallback

If you have multiple providers configured, you can set one as the **default**. If the default provider is unreachable, the system switches to the next active provider.

If no provider is available, the **rule-based fallback** activates: the system generates tip cards based on master data and the current phase — without a language model.

---

## Frequently Asked Questions

??? question "Can I use different providers for different features?"
    Currently, Kamerplanter uses the configured default provider for all AI features. Per-feature provider selection (e.g., local for chat, cloud for diagnosis) is planned for a future release.

??? question "How can I control cloud provider usage costs?"
    OpenAI and Anthropic provide usage dashboards and budget limits in their control panels. Tip cards are generated daily in the background and cached (4 hours), which significantly reduces consumption.

??? question "Ollama won't start or is unreachable — what should I do?"
    Check: (1) Is the Ollama service running? (`systemctl status ollama` on Linux). (2) Is Ollama on port 11434? (`curl http://localhost:11434`). (3) Is the model downloaded? (`ollama list`).

??? question "The model responds in a different language — what can I do?"
    Kamerplanter sends all requests in German and instructs the model to respond in German. If the model still responds in another language, try a larger model (`gemma3:4b` instead of `llama3.2:3b`).

---

## See Also

- [AI Assistant](ai-assistant.md)
- [Understanding the RAG Knowledge Base](../guides/rag-knowledge-base.md)
- [Environment Variables](../reference/environment-variables.md)
