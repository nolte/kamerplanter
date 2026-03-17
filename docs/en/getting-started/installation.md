# Installation

Before you can start Kamerplanter, you need Docker on your computer. This page explains what Docker is, how to install it, and how to verify everything is ready.

---

## What is Docker?

Docker is a tool that runs applications in so-called **containers**. A container includes everything an application needs — you don't have to install programming languages, databases, or other software yourself. Docker handles that for you.

Kamerplanter uses Docker to start five services (user interface, backend, database, cache, and background tasks) together. You only need a single command for that.

---

## Prerequisites

| What | Minimum | Recommended |
|------|---------|-------------|
| Operating system | Windows 10/11, macOS 12+, Linux (Ubuntu 22.04+, Debian 12+) | Linux |
| Memory (RAM) | 2 GB free | 4 GB free |
| Disk space | 3 GB free | 5 GB free |
| Internet connection | For initial download of container images | — |

---

## Install Docker

=== "Windows"

    1. Download **Docker Desktop**: [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
    2. Run the downloaded file and follow the installation wizard
    3. After installation, Docker Desktop starts automatically — you'll see the whale icon in the taskbar
    4. Open a **terminal** (PowerShell or Command Prompt) and verify the installation:

    ```powershell
    docker --version
    docker compose version
    ```

    !!! tip "WSL 2 required"
        Docker Desktop on Windows requires WSL 2 (Windows Subsystem for Linux). The installation wizard sets up WSL 2 automatically if it's not already present. A restart may be required.

=== "macOS"

    1. Download **Docker Desktop**: [docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop/)
    2. Open the `.dmg` file and drag Docker to the Applications folder
    3. Launch Docker from the Applications folder — macOS will ask for permissions on first launch
    4. Open a **terminal** and verify the installation:

    ```bash
    docker --version
    docker compose version
    ```

=== "Linux (Ubuntu/Debian)"

    Install Docker Engine via the official repository:

    ```bash
    # Update package index
    sudo apt-get update

    # Install dependencies
    sudo apt-get install -y ca-certificates curl

    # Add Docker's GPG key
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
      -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc

    # Add Docker repository
    echo "deb [arch=$(dpkg --print-architecture) \
      signed-by=/etc/apt/keyrings/docker.asc] \
      https://download.docker.com/linux/ubuntu \
      $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    # Install Docker
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli \
      containerd.io docker-compose-plugin

    # Add your user to the docker group (so you don't need sudo)
    sudo usermod -aG docker $USER
    ```

    !!! warning "Log out and back in"
        After adding yourself to the `docker` group, you must **log out and back in** (or restart) for the change to take effect.

    Verify the installation:

    ```bash
    docker --version
    docker compose version
    ```

=== "Raspberry Pi"

    The Raspberry Pi 4 (or newer) with at least 4 GB RAM works well for Kamerplanter. Use **Raspberry Pi OS (64-bit)**.

    ```bash
    # Install Docker via the official convenience script
    curl -fsSL https://get.docker.com | sudo sh

    # Add your user to the docker group
    sudo usermod -aG docker $USER
    ```

    After logging out and back in:

    ```bash
    docker --version
    docker compose version
    ```

---

## Verify installation

If Docker is installed correctly, you should see output similar to this:

```
$ docker --version
Docker version 27.x.x, build xxxxxxx

$ docker compose version
Docker Compose version v2.x.x
```

The exact version numbers may differ — what matters is that both commands work without errors.

!!! success "Ready!"
    Docker is installed? Continue with the [Quick Start](quickstart.md).

---

## Troubleshooting

??? question "docker: command not found"
    Docker is not installed or not in the system path. On Windows/macOS: Make sure Docker Desktop is running (whale icon in the taskbar). On Linux: Run the installation again.

??? question "permission denied while trying to connect to the Docker daemon socket"
    On Linux: Your user is not in the `docker` group. Run `sudo usermod -aG docker $USER` and log out and back in.

??? question "Docker Desktop won't start on Windows"
    Check if WSL 2 is installed: Open PowerShell as Administrator and run `wsl --install`. After a restart, Docker Desktop should start.

---

## See also

- [Quick Start](quickstart.md) — Start Kamerplanter in 5 minutes
- [First Deployment](first-deployment.md) — Run permanently on your own server
