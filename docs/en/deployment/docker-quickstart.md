# Docker Compose Quick Start

From zero to a running Kamerplanter instance with your first plants in 5 minutes.

!!! info "Prerequisite"
    Docker and Docker Compose must be installed. If not, follow the [Installation guide](docker-installation.md) first.

---

## 1. Download the repository

Download the source code and navigate to the directory:

```bash
git clone https://github.com/nolte/kamerplanter.git
cd kamerplanter
```

??? note "Don't have Git installed?"
    You can also download the repository as a ZIP file: Go to the [GitHub page](https://github.com/nolte/kamerplanter), click the green **Code** button and choose **Download ZIP**. Extract the file and open a terminal in the extracted folder.

---

## 2. Create configuration

Copy the example configuration and adjust the passwords:

```bash
cp .env.example .env
```

Open the `.env` file in a text editor and change at least the passwords:

```ini title=".env"
# Set secure passwords (at least 12 characters recommended)
ARANGO_ROOT_PASSWORD=your-secure-password      # (1)!
ARANGODB_PASSWORD=your-secure-password          # (2)!
```

1. The database password. Choose a secure password — it won't be shown in the browser.
2. Must be identical to `ARANGO_ROOT_PASSWORD`.

!!! tip "Generate a secure password"
    On Linux/macOS you can generate a random password:

    ```bash
    openssl rand -base64 24
    ```

    Copy the output and use it as the password in your `.env` file.

You can leave the remaining settings at their default values for now.

---

## 3. Start Kamerplanter

Start all services with a single command:

```bash
docker compose up -d
```

Docker downloads the required images on first start. This may take **2–5 minutes** depending on your internet connection. Subsequent starts are much faster.

Check that all services are running:

```bash
docker compose ps
```

You should see five services, all with status **running** or **healthy**:

```
NAME                  STATUS
kamerplanter-arangodb-1        running (healthy)
kamerplanter-valkey-1          running (healthy)
kamerplanter-backend-1         running (healthy)
kamerplanter-celery-worker-1   running
kamerplanter-celery-beat-1     running
kamerplanter-frontend-1        running (healthy)
```

??? question "A service shows 'unhealthy' or 'restarting'?"
    Wait 30 seconds and run `docker compose ps` again — some services take a bit longer to start. If the problem persists, check the logs:

    ```bash
    docker compose logs backend
    ```

---

## 4. Open Kamerplanter in your browser

Open your browser and go to:

**:point_right: [http://localhost:8080](http://localhost:8080)**

Since Kamerplanter starts in **Light Mode** by default, there is no login screen — you'll go straight to the Onboarding Wizard.

---

## 5. First-time setup

When you open Kamerplanter for the first time, it automatically starts the Onboarding Wizard. It guides you through experience level, location, and starter kit selection (e.g. "Windowsill Herbs" or "Houseplant Starter") in just a few minutes. Everything is self-explanatory and described in full on the [Onboarding Wizard](../user-guide/onboarding.md) page.

---

## Done!

Your Kamerplanter is running. From here you can:

- **View plants** and track growth status
- **Check tasks** created by the starter kit
- **Adjust locations** — rename rooms, add new ones
- **Add more plants** — via the "Master Data" menu

---

## Optional profiles (AI, sensor data)

The base start with `docker compose up -d` covers the full plant, task, and care workflow. Additional features — the AI knowledge assistant and sensor data history — can be enabled via optional **Docker Compose profiles**.

!!! note "Profiles are additive and combinable"
    Each profile extends the base setup with additional services. You can activate multiple profiles at the same time.

### Profile overview

| Profile | What it starts | Purpose | Required `.env` setting |
|---------|---------------|---------|------------------------|
| `vectordb` | PostgreSQL + pgvector (port 5433) + Reranker Service (port 8081) | AI/RAG knowledge assistant — semantic search in the knowledge base | `VECTORDB_ENABLED=true` |
| `ollama` | Ollama LLM server (port 11434) | Local LLM inference for the knowledge assistant, as an alternative to a cloud LLM API | `LLM_PROVIDER=ollama` and `LLM_API_URL=http://ollama:11434` |
| `timescaledb` | TimescaleDB (port 5432) | Time-series storage of sensor data (measurement history, automatic downsampling) | `TIMESCALEDB_ENABLED=true` |

### Example commands

**Base only (default — no profile needed):**

```bash
docker compose up -d
```

**AI knowledge assistant with local LLM (Ollama):**

```bash
docker compose --profile vectordb --profile ollama up -d
```

Then enable the services in your `.env`:

```ini title=".env"
VECTORDB_ENABLED=true
LLM_PROVIDER=ollama
LLM_API_URL=http://ollama:11434
LLM_MODEL=llama3.2          # Any model available in Ollama
```

!!! tip "Model download on first start"
    Ollama downloads the model on first use. Depending on the model, that is **4–15 GB** — plan your disk space accordingly.

**AI knowledge assistant with cloud LLM (e.g. Anthropic):**

```bash
docker compose --profile vectordb up -d
```

```ini title=".env"
VECTORDB_ENABLED=true
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-...
LLM_MODEL=claude-sonnet-4-20250514
```

**Sensor data history:**

```bash
docker compose --profile timescaledb up -d
```

```ini title=".env"
TIMESCALEDB_ENABLED=true
```

### Resource requirements per profile

!!! warning "Ollama requires significantly more resources"
    LLM models are large. For a smaller model (e.g. `llama3.2`) expect at least **8 GB of RAM** and **5 GB of free disk space**. Larger models need more. Without a dedicated GPU, inference runs on the CPU — slower, but functional.

| Profile | Additional RAM (typical) | Additional disk |
|---------|------------------------|-----------------|
| `vectordb` | ~512 MB | ~500 MB |
| `ollama` | 8–16 GB (depending on model) | 5–30 GB (depending on model) |
| `timescaledb` | ~256 MB | grows with sensor data |

---

## Useful commands

| Command | What it does |
|---------|-------------|
| `docker compose up -d` | Start all base services |
| `docker compose --profile vectordb --profile ollama up -d` | Start base + AI profiles |
| `docker compose --profile timescaledb up -d` | Start base + sensor data profile |
| `docker compose stop` | Stop all services (data is preserved) |
| `docker compose down` | Stop and remove containers (data is preserved) |
| `docker compose down -v` | Stop everything **and delete all data** (fresh start) |
| `docker compose logs -f backend` | Follow backend logs live |
| `docker compose ps` | Show status of all services |

!!! warning "Deleting data"
    The command `docker compose down -v` permanently deletes all stored data. Only use it if you want a complete fresh start.

---

## Access points

### Standard (always available)

| Service | URL | Description |
|---------|-----|-------------|
| User interface | [http://localhost:8080](http://localhost:8080) | The Kamerplanter app |
| API documentation | [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) | Interactive API reference (Swagger UI) |
| Database UI | [http://localhost:8529](http://localhost:8529) | ArangoDB web interface (for advanced users) |

### Optional (only with active profile)

| Service | URL | Profile | Description |
|---------|-----|---------|-------------|
| Reranker Service | [http://localhost:8081](http://localhost:8081) | `vectordb` | Cross-encoder for RAG quality |
| Ollama | [http://localhost:11434](http://localhost:11434) | `ollama` | Local LLM server (API) |

---

## See also

- [Onboarding Wizard](../user-guide/onboarding.md) — Detailed description of all wizard steps
- [Light Mode](../user-guide/light-mode.md) — What Light Mode means
- [First Deployment](docker-dauerbetrieb.md) — Run Kamerplanter permanently on your own server
