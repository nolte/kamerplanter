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

Since Kamerplanter starts in **Light Mode** by default, there is no login screen. You'll go straight to the Onboarding Wizard.

---

## 5. Walk through the Onboarding Wizard

The wizard guides you through setup in five steps:

### Step 1: Experience level

Choose how much experience you have with plant care:

- **Beginner** — Shows only the core features. Great for getting started.
- **Intermediate** — Adds fertilization, tanks, and sensors.
- **Expert** — All features visible.

You can change the level at any time later.

### Step 2: Environment & location

Describe where your plants are — e.g. "Kitchen window" or "South balcony". Kamerplanter uses this information to suggest suitable starter kits.

### Step 3: Choose a starter kit

Select a pre-configured scenario. The starter kit automatically creates matching plant species, growth phases, and fertilization plans.

| Starter Kit | For whom? |
|-------------|-----------|
| Windowsill Herbs | Basil, parsley & co. on the windowsill |
| Houseplant Starter | The most popular houseplants |
| Pet-Friendly Houseplants | Non-toxic plants for homes with pets |
| Balcony Tomatoes | Growing tomatoes on the balcony |
| Succulents & Cacti | Low-maintenance succulents |
| Mediterranean Herbs | Rosemary, thyme, oregano |
| Balcony Chillies | Chilli growing on the balcony |
| Vegetable Bed | Vegetables in an outdoor bed |
| Indoor Grow Tent | Controlled indoor growing |

### Step 4: Plants & favorites

Specify how many plants of each type you want to create, and mark your favorite plants.

### Step 5: Summary

Review the summary and click **Finish**. Kamerplanter creates everything automatically and takes you to the dashboard.

---

## Done!

Your Kamerplanter is running. From here you can:

- **View plants** and track growth status
- **Check tasks** created by the starter kit
- **Adjust locations** — rename rooms, add new ones
- **Add more plants** — via the "Master Data" menu

---

## Useful commands

| Command | What it does |
|---------|-------------|
| `docker compose up -d` | Start all services |
| `docker compose stop` | Stop all services (data is preserved) |
| `docker compose down` | Stop and remove containers (data is preserved) |
| `docker compose down -v` | Stop everything **and delete all data** (fresh start) |
| `docker compose logs -f backend` | Follow backend logs live |
| `docker compose ps` | Show status of all services |

!!! warning "Deleting data"
    The command `docker compose down -v` permanently deletes all stored data. Only use it if you want a complete fresh start.

---

## Access points

| Service | URL | Description |
|---------|-----|-------------|
| User interface | [http://localhost:8080](http://localhost:8080) | The Kamerplanter app |
| API documentation | [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) | Interactive API reference (Swagger UI) |
| Database UI | [http://localhost:8529](http://localhost:8529) | ArangoDB web interface (for advanced users) |

---

## See also

- [Onboarding Wizard](../user-guide/onboarding.md) — Detailed description of all wizard steps
- [Light Mode](../user-guide/light-mode.md) — What Light Mode means
- [First Deployment](docker-dauerbetrieb.md) — Run Kamerplanter permanently on your own server
