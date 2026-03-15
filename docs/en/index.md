# Welcome to Kamerplanter

Kamerplanter is a plant lifecycle management system — covering everything from seed to harvest. It supports vegetables, herbs, houseplants, and ornamentals with features like nutrient planning, phase tracking, sensor integration, and care reminders.

---

## What can Kamerplanter do?

<div class="grid cards" markdown>

-   **Master Data & Phases**

    ---

    Manage plant species, cultivars, and botanical families. Track every plant through its growth phases — from germination to harvest.

    [:octicons-arrow-right-24: User Guide](user-guide/index.md)

-   **Nutrient Planning**

    ---

    Plan fertilizer applications with EC budget calculations, mixing order validation, and flush protocols. Supports tap water, reverse osmosis, and mixed sources.

    [:octicons-arrow-right-24: Fertilization](user-guide/fertilization.md)

-   **Tank Management**

    ---

    Manage water tanks with fill level tracking, water source profiles (tap/RO), and automated dosage calculation.

    [:octicons-arrow-right-24: Tank Management](user-guide/tanks.md)

-   **Care Reminders**

    ---

    Adaptive watering and feeding schedules with 9 care preset profiles, seasonal awareness, and learning from confirmations.

    [:octicons-arrow-right-24: Tasks & Reminders](user-guide/tasks.md)

-   **Integrated Pest Management (IPM)**

    ---

    Three-tier system (prevention, monitoring, intervention) with pre-harvest interval enforcement that blocks harvests during active treatments.

    [:octicons-arrow-right-24: Pest Management](user-guide/pest-management.md)

-   **Calendar & Season Overview**

    ---

    Aggregated view of all tasks, phases, and events with iCal export. Sowing calendar for outdoor growing.

    [:octicons-arrow-right-24: Calendar](user-guide/calendar.md)

</div>

---

## Quick Start

=== "Docker Compose (simple)"

    ```bash
    docker compose up --build
    ```

    This starts the backend, frontend, ArangoDB, and Redis.

    **Demo login:** `demo@kamerplanter.local` / `demo-passwort-2024`

=== "Skaffold (development)"

    ```bash
    skaffold dev --trigger=manual --port-forward
    ```

    Skaffold is the primary tool for local development.

    [:octicons-arrow-right-24: Local Setup](development/local-setup.md)

---

## Project Background

!!! note "Origin Story"
    This project started as a **vibe coding experiment** — built almost entirely through conversational AI prompting with Claude Code. The specifications, architecture, domain models, backend, frontend, Helm charts, and tests were all developed in this style. What began as an exploration of AI-assisted development grew into a fully functional agricultural management platform.

---

## Navigating the Docs

| Section | Description |
|---------|-------------|
| [Getting Started](getting-started/index.md) | Installation, quick start, first deployment |
| [User Guide](user-guide/index.md) | All features explained for end users |
| [Architecture](architecture/index.md) | System design, layers, data models |
| [Development](development/index.md) | Local setup, code standards, testing |
| [API](api/index.md) | REST API reference, authentication |
| [Deployment](deployment/index.md) | Kubernetes, Helm, CI/CD |
| [Guides](guides/index.md) | Deep-dive guides for GDD, VPD, nutrients |
| [ADR](adr/index.md) | Architecture Decision Records |
