# Docker Compose Permanent Operation

You've tried Kamerplanter in the [Quick Start](docker-quickstart.md) and now want to run it permanently? This guide shows you how to set up Kamerplanter on your own server — for example on a Raspberry Pi, NAS, or home server.

---

## Difference from Quick Start

In the Quick Start, you built Kamerplanter from source code (`docker compose up`). For permanent operation, you use **pre-built images** instead — this is faster, uses less storage, and you don't need the source code on the server.

| | Quick Start | Permanent deployment |
|---|---|---|
| Docker Compose file | `docker-compose.yml` | `docker-compose.release.yml` |
| Images | Built locally | Pre-built from registry |
| Source code needed? | Yes | No |
| Restart on crash | Manual | Automatic |
| Suitable for | Trying out, development | Permanent operation |

---

## Prerequisites

- A server with Docker and Docker Compose (see [Installation](docker-installation.md))
- At least 2 GB RAM (4 GB recommended)
- Stable network connection for downloading images

---

## 1. Download project files

You only need two files from the repository — not the entire source code:

```bash
# Create directory
mkdir -p ~/kamerplanter && cd ~/kamerplanter

# Download the two required files
curl -O https://raw.githubusercontent.com/nolte/kamerplanter/main/docker-compose.release.yml
curl -O https://raw.githubusercontent.com/nolte/kamerplanter/main/.env.example
```

---

## 2. Create configuration

```bash
cp .env.example .env
```

Open the `.env` file and set **secure passwords**:

```ini title=".env"
# Generate secure passwords: openssl rand -base64 24
ARANGO_ROOT_PASSWORD=insert-secure-password-here
ARANGODB_PASSWORD=insert-secure-password-here

# Defaults — change only if needed
ARANGODB_DATABASE=kamerplanter
ARANGODB_USERNAME=root
REDIS_URL=redis://valkey:6379/0
DEBUG=false
REQUIRE_EMAIL_VERIFICATION=false
CORS_ORIGINS=["http://localhost:8080"]
```

!!! warning "Passwords"
    Do **not** use the example passwords from `.env.example`. Generate secure passwords, e.g. with `openssl rand -base64 24`. Both password fields (`ARANGO_ROOT_PASSWORD` and `ARANGODB_PASSWORD`) must be identical.

### Three additional mandatory secrets (otherwise the backend won't start)

!!! danger "Without these three values the backend start-up aborts"
    `.env.example` sets `DEBUG=false` — the correct value for permanent operation. With `DEBUG=false` the backend additionally checks `JWT_SECRET_KEY`, `FERNET_KEY` and `ERASURE_TOMBSTONE_SALT` at start-up and aborts with an error if any of them is missing (fail-fast gate). `docker-compose.release.yml` does **not** automatically pass these three variables into the backend container — you have to add them yourself.

Generate the three values and add them to your `.env`:

```bash
# JWT_SECRET_KEY and ERASURE_TOMBSTONE_SALT (at least 32 characters)
openssl rand -hex 32

# FERNET_KEY (must be a valid Fernet key)
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

```ini title=".env"
JWT_SECRET_KEY=<output of openssl rand -hex 32>
FERNET_KEY=<output of the Fernet command>
ERASURE_TOMBSTONE_SALT=<second output of openssl rand -hex 32>
```

Also create a `docker-compose.override.yml` next to `docker-compose.release.yml` — Docker Compose loads it automatically:

```yaml title="docker-compose.override.yml"
services:
  backend:
    environment:
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      FERNET_KEY: ${FERNET_KEY}
      ERASURE_TOMBSTONE_SALT: ${ERASURE_TOMBSTONE_SALT}
  celery-worker:
    environment:
      FERNET_KEY: ${FERNET_KEY}
      ERASURE_TOMBSTONE_SALT: ${ERASURE_TOMBSTONE_SALT}
  celery-beat:
    environment:
      FERNET_KEY: ${FERNET_KEY}
      ERASURE_TOMBSTONE_SALT: ${ERASURE_TOMBSTONE_SALT}
```

Full overview of every mandatory secret per feature: [Configuration Matrix — Mandatory secrets](konfigurationsmatrix.md#pflicht-secrets-je-aktivierter-funktion).

!!! warning "Reference both Compose files from now on"
    Since you created an additional `docker-compose.override.yml`, every `docker compose` command from here on must reference **both** files: `-f docker-compose.release.yml -f docker-compose.override.yml`. All following commands on this page assume that.

---

## 3. Set the version

The file `docker-compose.release.yml` contains `__VERSION__` as a placeholder. Replace it with the desired version:

```bash
# Example: set version 1.0.0
sed -i 's/__VERSION__/1.0.0/g' docker-compose.release.yml
```

??? note "Which version should I use?"
    Use the latest stable version. You can find available versions on the project's [Releases page](https://github.com/nolte/kamerplanter/releases).

---

## 4. Start

```bash
docker compose -f docker-compose.release.yml -f docker-compose.override.yml up -d
```

Check the status:

```bash
docker compose -f docker-compose.release.yml -f docker-compose.override.yml ps
```

All services should show as **running** or **healthy** after 30–60 seconds.

---

## 5. Test access

Open in your browser:

- **Kamerplanter:** [http://your-server:8080](http://localhost:8080)
- **API documentation:** [http://your-server:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

Replace `your-server` with the IP address or hostname of your server. If you're working on the server itself, `localhost` works.

---

## Automatic restart

The release configuration already includes `restart: unless-stopped` for all services. This means:

- After a server crash or reboot, Docker restarts the services automatically
- Services you deliberately stop with `docker compose stop` stay stopped

To ensure Docker itself starts after a reboot:

```bash
sudo systemctl enable docker
```

---

## Performing updates

To update Kamerplanter to a new version:

```bash
cd ~/kamerplanter

# 1. Update version in the Compose file
sed -i 's/old-version/new-version/g' docker-compose.release.yml

# 2. Pull new images and restart services
docker compose -f docker-compose.release.yml -f docker-compose.override.yml pull
docker compose -f docker-compose.release.yml -f docker-compose.override.yml up -d

# 3. Clean up old, unused images (optional)
docker image prune -f
```

!!! tip "Data is preserved"
    Your plants, locations, and all other data are stored in Docker volumes and survive updates without issues.

---

## Backups

Kamerplanter's data lives in two Docker volumes:

- `arangodb_data` — All plants, locations, tasks, and configurations
- `valkey_data` — Cache and task queue (not critical, rebuilt automatically)

### Create a backup

```bash
# Back up ArangoDB data
docker compose -f docker-compose.release.yml -f docker-compose.override.yml exec arangodb \
  arangodump --server.password "$ARANGO_ROOT_PASSWORD" \
  --output-directory /tmp/backup --overwrite true

# Copy backup from the container
docker compose -f docker-compose.release.yml -f docker-compose.override.yml cp \
  arangodb:/tmp/backup ./backup-$(date +%Y%m%d)
```

### Restore a backup

```bash
# Copy backup into the container
docker compose -f docker-compose.release.yml -f docker-compose.override.yml cp \
  ./backup-20260317 arangodb:/tmp/backup

# Restore data
docker compose -f docker-compose.release.yml -f docker-compose.override.yml exec arangodb \
  arangorestore --server.password "$ARANGO_ROOT_PASSWORD" \
  --input-directory /tmp/backup --overwrite true
```

!!! tip "Regular backups"
    Set up a cron job to run backups automatically — for example daily at 3:00 AM. That way you'll lose at most one day of data in the worst case.

---

## Accessing from other devices

By default, Kamerplanter is only accessible from the server itself. To access it from your smartphone, tablet, or other computers on your home network:

1. Find your server's IP address:

    ```bash
    hostname -I
    ```

2. On the other device, open a browser and go to `http://<IP-address>:8080`

3. Update the CORS setting in `.env` so the API accepts requests from the new address:

    ```ini title=".env"
    CORS_ORIGINS=["http://localhost:8080","http://192.168.1.100:8080"]
    ```

4. Restart the services after the change:

    ```bash
    docker compose -f docker-compose.release.yml -f docker-compose.override.yml up -d
    ```

---

## Next steps

- [Onboarding Wizard](../user-guide/onboarding.md) — Set up your first plants
- [User Guide](../user-guide/index.md) — All features in detail
- [Kubernetes Deployment](../deployment/kubernetes.md) — For professional environments with high availability

---

## Troubleshooting

??? question "Page won't load (connection refused)"
    Check if all services are running: `docker compose -f docker-compose.release.yml -f docker-compose.override.yml ps`. If the frontend service isn't running, check the logs: `docker compose -f docker-compose.release.yml -f docker-compose.override.yml logs frontend`.

??? question "Backend reports 'Connection refused' to the database"
    ArangoDB takes a bit longer on first start. Wait 30 seconds and check again. If the error persists: Do the passwords in `.env` match? `ARANGO_ROOT_PASSWORD` and `ARANGODB_PASSWORD` must be identical.

??? question "Can't access from another device"
    Check: (1) Are both devices on the same network? (2) Is the IP address correct? (3) Is the CORS setting in `.env` updated? (4) Is a firewall blocking port 8080?

??? question "How much disk space does Kamerplanter need long-term?"
    The Docker images take about 2 GB. The database grows depending on usage — for a typical home user with up to 100 plants, data stays under 100 MB. Sensor data can grow faster when recording is enabled.
