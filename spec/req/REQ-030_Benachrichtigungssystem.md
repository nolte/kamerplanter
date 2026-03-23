# Spezifikation: REQ-030 - Benachrichtigungssystem mit Home Assistant Integration

```yaml
ID: REQ-030
Titel: Multi-Kanal-Benachrichtigungssystem mit Home Assistant als primaerem Zustellkanal
Kategorie: Pflege & Kommunikation
Fokus: Beides
Technologie: Python, FastAPI, Celery, Redis, ArangoDB, React, TypeScript, MUI, Home Assistant
Status: Entwurf
Version: 1.0
Abhaengigkeit: REQ-022 v2.4 (Pflegeerinnerungen), REQ-006 v2.7 (Aufgabenplanung), REQ-018 v1.0 (Umgebungssteuerung), REQ-024 v1.3 (Mandantenverwaltung), REQ-023 v1.7 (Service Accounts)
```

## 1. Business Case

**User Story (Zimmerpflanzen-Giessen):** "Als Zimmerpflanzen-Besitzerin moechte ich eine Push-Nachricht auf mein Handy bekommen, wenn meine Monstera gegossen werden muss — nicht erst sehen, dass es faellig war, wenn ich abends die App oeffne."

**User Story (HA-Benachrichtigung):** "Als Home-Assistant-Nutzer moechte ich, dass Kamerplanter-Erinnerungen als HA-Notifications auf meinem Handy und meinen Dashboards erscheinen — damit ich ein einziges Benachrichtigungszentrum fuer mein Smart Home habe, statt noch eine weitere App checken zu muessen."

**User Story (HA-Automation):** "Als Smart-Home-Enthusiast moechte ich auf Kamerplanter-Benachrichtigungen mit HA-Automationen reagieren koennen — z.B. bei 'Giessen faellig' automatisch die Bewaesserungsventile oeffnen oder bei 'Frostwarnung' die Gewaechshausheizung einschalten."

**User Story (Actionable Notification):** "Als Nutzer moechte ich direkt in der HA-Benachrichtigung einen Button 'Erledigt' haben — damit ich die Giesserinnerung mit einem Tap bestaetigen kann, ohne die Kamerplanter-App oeffnen zu muessen."

**User Story (Eskalation):** "Als vergesslicher Pflanzenpfleger moechte ich, dass ueberfaellige Erinnerungen nach 2 Tagen erneut gesendet werden und nach 4 Tagen als kritisch markiert werden — damit ich wirklich keine Pflanze verdursten lasse."

**User Story (Multi-Kanal):** "Als Nutzer ohne Home Assistant moechte ich Benachrichtigungen trotzdem per E-Mail oder PWA-Push erhalten koennen — die HA-Integration soll optional sein."

**User Story (HA-TTS):** "Als Nutzer mit smarten Lautsprechern moechte ich morgens eine Sprachansage hoeren: 'Heute muessen 3 Pflanzen gegossen werden: Monstera, Ficus und Basilikum' — damit ich beim Fruehstueck schon weiss, was ansteht."

**User Story (HA-Dashboard-Widget):** "Als HA-Nutzer moechte ich eine Kamerplanter-Benachrichtigungskarte auf meinem Dashboard sehen, die alle faelligen Pflegeaufgaben mit Dringlichkeit anzeigt — wie ein Mini-Pflege-Dashboard direkt in Home Assistant."

**Beschreibung:**

REQ-022 (Pflegeerinnerungen) generiert bereits taeglich Celery-Tasks fuer faellige Pflege-Aktionen. REQ-006 (Aufgabenplanung) hat ein vollstaendiges Task-System. Was fehlt: **der Zustellkanal zum Nutzer**. Die Erinnerungen existieren nur in der Datenbank — der Nutzer erfaehrt erst davon, wenn er die App aktiv oeffnet.

REQ-030 schliesst diese Luecke mit einem **Multi-Kanal-Benachrichtigungssystem**, das Home Assistant als **primaeren und leistungsfaehigsten Zustellkanal** integriert:

**Kernkonzepte:**

**Home Assistant als Notification Hub:**
HA ist fuer Smart-Home-Nutzer bereits das zentrale Benachrichtigungszentrum (Companion App Push, TTS, Dashboards, Actionable Notifications). Statt ein eigenes Push-System zu bauen, nutzt Kamerplanter die vorhandene HA-Infrastruktur:
- **HA Events** (`kamerplanter_notification`) — Notifications als Events feuern, die von HA-Automationen verarbeitet werden
- **HA Persistent Notifications** — Direkt im HA-Frontend sichtbar
- **HA Mobile Push** — Via HA Companion App (Android/iOS), mit Actionable Buttons
- **HA TTS** — Sprachansagen auf smarten Lautsprechern
- **HA Dashboard Cards** — Custom Lovelace-Card fuer Pflege-Uebersicht

**Adapter-Pattern fuer Kanaeale ohne HA:**
Fuer Nutzer ohne Home Assistant stehen alternative Kanaele bereit:
- **E-Mail** (SMTP) — Erweitert die bestehende `IEmailService`-Implementierung
- **PWA Push** (Web Push API / Service Worker) — Fuer Browser-Nutzer
- **Apprise** (Optional) — 100+ Dienste (Telegram, Slack, Pushover, Gotify, ntfy, Discord, etc.)

**Drei-Schichten-Architektur:**
```
REQ-022 CareReminderEngine ──┐
REQ-006 TaskEngine ──────────┼──▶ NotificationEngine ──▶ INotificationChannel
REQ-018 ActuatorEngine ──────┤       (Routing, Throttle,     ├── HomeAssistantChannel (primaer)
REQ-010 IPM Alerts ──────────┤        Eskalation, Batching)  ├── EmailChannel
REQ-005 Sensor Alerts ───────┘                                ├── PwaChannel
                                                              ├── AppriseChannel (optional)
                                                              └── InAppChannel (Fallback)
```

**Grundprinzipien:**

- **HA-First:** Home Assistant ist der bevorzugte Zustellkanal — reichste Interaktion (Actionable Buttons, TTS, Dashboard), keine zusaetzliche App noetig
- **Vollstaendig optional:** Ohne HA und ohne Kanal-Konfiguration funktioniert die App mit In-App-Notifications (Pflege-Dashboard REQ-022)
- **Adapter-Pattern:** Neue Kanaele durch Registrierung anbindbar (wie REQ-011 Source Adapters)
- **Batching:** Mehrere faellige Erinnerungen werden zu einer Nachricht zusammengefasst ("3 Pflanzen giessen heute")
- **Eskalation:** Ueberfaellige Aufgaben werden re-notifiziert mit steigender Dringlichkeit
- **Idempotenz:** Gleiche Notification wird nicht doppelt gesendet (Dedup via Redis)
- **Quiet Hours:** Keine Benachrichtigungen ausserhalb konfigurierter Zeiten

### 1.1 Notification-Typen

| Typ | Schluessel | Quelle | Dringlichkeit | HA-Event-Type | Beispiel |
|-----|-----------|--------|---------------|---------------|---------|
| Giess-Erinnerung | `care.watering` | REQ-022 | normal → high (nach 2d) | `kamerplanter_care_due` | "Monstera: Giessen faellig" |
| Duenge-Erinnerung | `care.fertilizing` | REQ-022 | normal | `kamerplanter_care_due` | "3 Pflanzen duengen (Maerz-Duengung)" |
| Umtopf-Erinnerung | `care.repotting` | REQ-022 | low | `kamerplanter_care_due` | "Ficus: Umtopfen empfohlen (18 Monate)" |
| Schaedlingskontrolle | `care.pest_check` | REQ-022 | normal | `kamerplanter_care_due` | "Schaedlingskontrolle: 5 Pflanzen pruefen" |
| Winterschutz | `care.winter_protection` | REQ-022 | critical | `kamerplanter_seasonal` | "ACHTUNG: 4 Pflanzen brauchen Winterschutz!" |
| Fruehlings-Auspacken | `care.spring_uncover` | REQ-022 | high | `kamerplanter_seasonal` | "3 Pflanzen koennen raus / abgedeckt werden" |
| Knollen ausgraben | `care.tuber_dig` | REQ-022 | critical | `kamerplanter_seasonal` | "DRINGEND: Dahlienknollen vor Frost ausgraben!" |
| Phasen-Uebergang | `phase.transition` | REQ-003 | normal | `kamerplanter_phase` | "Basilikum: Bluetephase erreicht" |
| Sensor-Alarm | `sensor.alert` | REQ-005 | high–critical | `kamerplanter_sensor_alert` | "Temperatur Gewaechshaus: 4°C (Frostgrenze!)" |
| IPM-Alarm | `ipm.alert` | REQ-010 | high | `kamerplanter_ipm_alert` | "Spinnmilben erkannt bei Monstera" |
| Karenz-Ablauf | `ipm.karenz_end` | REQ-010 | normal | `kamerplanter_ipm_alert` | "Karenzzeit abgelaufen: Tomate erntereif" |
| Tank leer | `tank.low` | REQ-014 | high | `kamerplanter_tank_alert` | "Tank A: Fuellstand unter 20%" |
| Ernte bereit | `harvest.ready` | REQ-007 | normal | `kamerplanter_harvest` | "Tomaten: Erntebereitschaft erkannt" |
| Task faellig | `task.due` | REQ-006 | normal | `kamerplanter_task_due` | "Aufgabe faellig: Obstbaumschnitt" |
| Frostwarnung | `weather.frost` | REQ-005 | critical | `kamerplanter_weather_alert` | "Frostwarnung morgen Nacht: -3°C erwartet" |

### 1.2 Eskalationsstufen

```
Tag 0 (faellig)     →  Normale Benachrichtigung
Tag +2 (ueberfaellig) →  Wiederholung, Dringlichkeit "high"
Tag +4 (kritisch)    →  Wiederholung, Dringlichkeit "critical"
Tag +7 (aufgegeben)  →  Letzte Warnung, danach Stille (Notification Fatigue vermeiden)
```

Eskalation ist **nur fuer Giess-Erinnerungen** aktiv — eine nicht gegossene Pflanze stirbt. Fuer andere Typen (Duengen, Umtopfen, Schaedlingskontrolle) wird maximal einmal erinnert.

## 2. Datenmodell-Erweiterung (ArangoDB)

### Neue Collections:

**`notifications` (Document Collection):**
```json
{
  "_key": "notif_20260321_abc123",
  "tenant_key": "tenant_personal_anna",
  "user_key": "user_anna",
  "notification_type": "care.watering",
  "title": "3 Pflanzen gießen",
  "body": "Monstera, Ficus und Basilikum brauchen heute Wasser.",
  "urgency": "normal",
  "data": {
    "plant_keys": ["plant_monstera_01", "plant_ficus_01", "plant_basilikum_01"],
    "task_keys": ["task_care_water_001", "task_care_water_002", "task_care_water_003"],
    "action_url": "/pflege"
  },
  "channels_sent": ["home_assistant", "email"],
  "channels_failed": [],
  "ha_event_type": "kamerplanter_care_due",
  "status": "delivered",
  "read_at": null,
  "acted_at": "2026-03-21T09:15:00Z",
  "escalation_level": 0,
  "parent_notification_key": null,
  "created_at": "2026-03-21T06:00:00Z"
}
```

**`notification_preferences` (Document Collection):**
```json
{
  "_key": "notifpref_user_anna",
  "user_key": "user_anna",
  "channels": {
    "home_assistant": {
      "enabled": true,
      "priority": 1,
      "config": {
        "persistent_notification": true,
        "mobile_push": true,
        "tts_entity_id": "media_player.kueche",
        "tts_enabled": false,
        "actionable_buttons": true
      }
    },
    "email": {
      "enabled": true,
      "priority": 2,
      "config": {
        "address": "anna@example.com",
        "digest_mode": "daily",
        "digest_time": "07:00"
      }
    },
    "pwa": {
      "enabled": false,
      "priority": 3,
      "config": {}
    },
    "apprise": {
      "enabled": false,
      "priority": 4,
      "config": {
        "urls": []
      }
    }
  },
  "quiet_hours": {
    "enabled": true,
    "start": "22:00",
    "end": "07:00",
    "timezone": "Europe/Berlin"
  },
  "batching": {
    "enabled": true,
    "window_minutes": 30,
    "max_batch_size": 10
  },
  "escalation": {
    "watering_enabled": true,
    "escalation_days": [2, 4, 7]
  },
  "type_overrides": {
    "care.watering": { "channels": ["home_assistant", "email"] },
    "sensor.alert": { "channels": ["home_assistant"], "ignore_quiet_hours": true },
    "weather.frost": { "channels": ["home_assistant"], "ignore_quiet_hours": true },
    "care.repotting": { "channels": ["email"] }
  },
  "daily_summary": {
    "enabled": true,
    "time": "07:00",
    "channel": "home_assistant"
  }
}
```

### Neue Edges:

```aql
// Edge Collection: notification_for_task (notifications → tasks)
//   Verbindet Notification mit dem ausloesenden Task (REQ-006/REQ-022)
//   Felder: notification_type, created_at

// Edge Collection: notification_for_run (notifications → planting_runs)
//   Verbindet Notification mit betroffenen Runs (REQ-013 v2.0: Run-Level, ex notification_for_plant)

// Edge Collection: user_has_notification_prefs (users → notification_preferences)
//   1:1, Nutzer hat Benachrichtigungseinstellungen
```

## 3. Technische Umsetzung (Python)

### 3.1 Notification Channel Interface

```python
from abc import ABC, abstractmethod
from enum import StrEnum
from pydantic import BaseModel, Field


class NotificationUrgency(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationAction(BaseModel):
    """Actionable Button in einer Notification."""
    action_id: str             # z.B. "confirm_watering"
    title: str                 # z.B. "Erledigt"
    uri: str | None = None     # Deep-Link in die App


class Notification(BaseModel):
    """Kanal-unabhaengiges Notification-Objekt."""
    notification_key: str
    notification_type: str         # z.B. "care.watering"
    title: str
    body: str
    urgency: NotificationUrgency = NotificationUrgency.NORMAL
    data: dict = Field(default_factory=dict)
    actions: list[NotificationAction] = Field(default_factory=list)
    image_url: str | None = None   # Optionales Bild (z.B. Pflanzenfoto)
    group_key: str | None = None   # Fuer Batching
    ha_event_type: str | None = None


class ChannelResult(BaseModel):
    """Ergebnis eines Zustellversuchs."""
    channel_key: str
    success: bool
    error: str | None = None
    external_id: str | None = None  # z.B. HA Event-ID


class INotificationChannel(ABC):
    """Basis-Interface fuer Benachrichtigungskanaele.

    Adapter-Pattern analog zu ExternalSourceAdapter (REQ-011)
    und PlantIdentificationAdapter (REQ-029).
    """

    @property
    @abstractmethod
    def channel_key(self) -> str:
        """Eindeutiger Schluessel des Kanals (z.B. 'home_assistant')."""

    @property
    @abstractmethod
    def supports_actions(self) -> bool:
        """True wenn Kanal Actionable Buttons unterstuetzt."""

    @property
    @abstractmethod
    def supports_batching(self) -> bool:
        """True wenn Kanal mehrere Notifications zusammenfassen kann."""

    @abstractmethod
    async def send(
        self,
        notification: Notification,
        channel_config: dict,
    ) -> ChannelResult:
        """Sendet eine einzelne Notification.

        Args:
            notification: Die zu sendende Benachrichtigung
            channel_config: Nutzer-spezifische Kanal-Konfiguration

        Returns:
            ChannelResult mit Erfolg/Fehler
        """

    async def send_batch(
        self,
        notifications: list[Notification],
        channel_config: dict,
    ) -> ChannelResult:
        """Sendet mehrere Notifications als Batch (Default: einzeln senden)."""
        results = []
        for n in notifications:
            results.append(await self.send(n, channel_config))
        success = all(r.success for r in results)
        errors = [r.error for r in results if r.error]
        return ChannelResult(
            channel_key=self.channel_key,
            success=success,
            error="; ".join(errors) if errors else None,
        )

    async def health_check(self) -> bool:
        """Prueft ob der Kanal erreichbar ist."""
        return True
```

### 3.2 Home Assistant Notification Channel (Primaer)

```python
import structlog
from app.data_access.external.ha_client import HomeAssistantClient

logger = structlog.get_logger()


class HomeAssistantNotificationChannel(INotificationChannel):
    """Benachrichtigungen via Home Assistant.

    Nutzt drei HA-Mechanismen:
    1. HA Events — fuer Automationen (kamerplanter_care_due, kamerplanter_sensor_alert, ...)
    2. Persistent Notifications — sichtbar im HA-Frontend
    3. Mobile Push (via Companion App Service) — Actionable Notifications auf dem Handy

    Die HA Custom Integration (kamerplanter-ha) empfaengt die Events
    und kann sie per Automation an beliebige HA-Notify-Services weiterleiten
    (Companion App, TTS, Telegram Bot, Alexa, etc.).
    """

    channel_key = "home_assistant"
    supports_actions = True
    supports_batching = True

    def __init__(self, ha_client: HomeAssistantClient) -> None:
        self._ha = ha_client

    async def send(
        self,
        notification: Notification,
        channel_config: dict,
    ) -> ChannelResult:
        try:
            # 1. HA Event feuern (fuer Automationen)
            event_data = {
                "notification_key": notification.notification_key,
                "type": notification.notification_type,
                "title": notification.title,
                "body": notification.body,
                "urgency": notification.urgency.value,
                "data": notification.data,
                "actions": [a.model_dump() for a in notification.actions],
            }

            if notification.ha_event_type:
                await self._ha.fire_event(
                    notification.ha_event_type,
                    event_data,
                )

            # 2. Persistent Notification (im HA-Frontend sichtbar)
            if channel_config.get("persistent_notification", True):
                await self._ha.create_persistent_notification(
                    title=notification.title,
                    message=notification.body,
                    notification_id=f"kp_{notification.notification_key}",
                )

            # 3. Mobile Push via Companion App (wenn konfiguriert)
            if channel_config.get("mobile_push", True):
                push_data = {
                    "title": notification.title,
                    "message": notification.body,
                    "data": {
                        "group": notification.group_key or notification.notification_type,
                        "tag": notification.notification_key,
                        "importance": self._map_urgency_to_importance(notification.urgency),
                        "channel": "kamerplanter_care",
                        "clickAction": notification.data.get("action_url", "/pflege"),
                    },
                }

                # Actionable Buttons (HA Companion App)
                if notification.actions and channel_config.get("actionable_buttons", True):
                    push_data["data"]["actions"] = [
                        {
                            "action": action.action_id,
                            "title": action.title,
                            "uri": action.uri,
                        }
                        for action in notification.actions
                    ]

                if notification.image_url:
                    push_data["data"]["image"] = notification.image_url

                # Service-Call an alle HA Mobile-App-Notify-Services
                await self._ha.call_service(
                    "notify", "mobile_app_companion",
                    service_data=push_data,
                )

            # 4. TTS (optional)
            tts_entity = channel_config.get("tts_entity_id")
            if tts_entity and channel_config.get("tts_enabled", False):
                await self._ha.call_service(
                    "tts", "speak",
                    service_data={
                        "entity_id": tts_entity,
                        "message": notification.body,
                        "language": "de",
                    },
                )

            return ChannelResult(
                channel_key=self.channel_key,
                success=True,
                external_id=f"ha_event_{notification.notification_key}",
            )

        except Exception as exc:
            logger.error(
                "ha_notification_failed",
                notification_key=notification.notification_key,
                error=str(exc),
            )
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error=str(exc),
            )

    async def send_batch(
        self,
        notifications: list[Notification],
        channel_config: dict,
    ) -> ChannelResult:
        """Fasst mehrere Pflegeerinnerungen zu einer Nachricht zusammen."""
        if len(notifications) <= 1:
            return await self.send(notifications[0], channel_config)

        # Batch-Notification erstellen
        care_items = [n.title for n in notifications]
        plant_keys = []
        task_keys = []
        for n in notifications:
            plant_keys.extend(n.data.get("plant_keys", []))
            task_keys.extend(n.data.get("task_keys", []))

        batch = Notification(
            notification_key=f"batch_{notifications[0].notification_key}",
            notification_type=notifications[0].notification_type,
            title=f"{len(notifications)} Pflegeaufgaben heute",
            body="\n".join(f"- {item}" for item in care_items),
            urgency=max(n.urgency for n in notifications),
            data={
                "plant_keys": plant_keys,
                "task_keys": task_keys,
                "action_url": "/pflege",
                "batch_count": len(notifications),
            },
            actions=[
                NotificationAction(
                    action_id="open_care_dashboard",
                    title="Pflege-Dashboard oeffnen",
                    uri="/pflege",
                ),
            ],
            ha_event_type="kamerplanter_care_due",
        )

        return await self.send(batch, channel_config)

    @staticmethod
    def _map_urgency_to_importance(urgency: NotificationUrgency) -> str:
        return {
            NotificationUrgency.LOW: "low",
            NotificationUrgency.NORMAL: "default",
            NotificationUrgency.HIGH: "high",
            NotificationUrgency.CRITICAL: "high",
        }[urgency]
```

### 3.3 Home Assistant Client Erweiterung

```python
# Erweiterung von src/backend/app/data_access/external/ha_client.py

class HomeAssistantClient:
    """Erweiterter HTTP-Client fuer Home Assistant REST API.

    Bestehende Methoden (REQ-018):
    - list_sensor_entities()
    - get_state(entity_id)

    Neue Methoden (REQ-030):
    - fire_event(event_type, event_data)
    - create_persistent_notification(title, message, notification_id)
    - call_service(domain, service, service_data)
    - dismiss_persistent_notification(notification_id)
    """

    async def fire_event(
        self,
        event_type: str,
        event_data: dict,
    ) -> dict:
        """Feuert ein HA Event (POST /api/events/{event_type}).

        Events werden von HA-Automationen verarbeitet.
        Die Kamerplanter HA-Integration registriert Listener fuer:
        - kamerplanter_care_due
        - kamerplanter_seasonal
        - kamerplanter_sensor_alert
        - kamerplanter_ipm_alert
        - kamerplanter_tank_alert
        - kamerplanter_harvest
        - kamerplanter_task_due
        - kamerplanter_weather_alert
        - kamerplanter_phase
        """
        # POST /api/events/{event_type}
        ...

    async def create_persistent_notification(
        self,
        title: str,
        message: str,
        notification_id: str,
    ) -> None:
        """Erstellt eine persistente Notification im HA-Frontend.

        POST /api/services/persistent_notification/create
        """
        ...

    async def call_service(
        self,
        domain: str,
        service: str,
        service_data: dict,
    ) -> dict:
        """Ruft einen HA-Service auf (POST /api/services/{domain}/{service}).

        Wird fuer Mobile Push (notify.mobile_app_xxx) und TTS (tts.speak) genutzt.
        """
        ...

    async def dismiss_persistent_notification(
        self,
        notification_id: str,
    ) -> None:
        """Entfernt eine persistente Notification (nach Bestaetigung).

        POST /api/services/persistent_notification/dismiss
        """
        ...
```

### 3.4 Email Notification Channel

```python
class EmailNotificationChannel(INotificationChannel):
    """Benachrichtigungen per E-Mail.

    Erweitert die bestehende IEmailService-Implementierung (REQ-023)
    um Pflege-Notifications. Unterstuetzt Einzel-Mails und Daily Digest.
    """

    channel_key = "email"
    supports_actions = False  # E-Mail hat keine Actionable Buttons
    supports_batching = True

    def __init__(self, email_service) -> None:
        self._email = email_service

    async def send(
        self,
        notification: Notification,
        channel_config: dict,
    ) -> ChannelResult:
        address = channel_config.get("address")
        if not address:
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error="No email address configured",
            )

        # Digest-Modus: Einzelne Notifications werden gesammelt
        digest_mode = channel_config.get("digest_mode", "immediate")
        if digest_mode == "daily":
            # In Redis-Queue fuer Daily Digest einreihen
            await self._enqueue_for_digest(address, notification)
            return ChannelResult(channel_key=self.channel_key, success=True)

        # Sofort senden
        await self._email.send_notification_email(
            to_email=address,
            subject=notification.title,
            body_html=self._render_html(notification),
        )

        return ChannelResult(channel_key=self.channel_key, success=True)

    async def send_batch(
        self,
        notifications: list[Notification],
        channel_config: dict,
    ) -> ChannelResult:
        """Sendet Batch als eine zusammengefasste E-Mail."""
        address = channel_config.get("address")
        if not address:
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error="No email address configured",
            )

        subject = f"Kamerplanter: {len(notifications)} Pflegeaufgaben heute"
        body = self._render_digest_html(notifications)

        await self._email.send_notification_email(
            to_email=address,
            subject=subject,
            body_html=body,
        )

        return ChannelResult(channel_key=self.channel_key, success=True)
```

### 3.5 PWA Push Channel

```python
class PwaNotificationChannel(INotificationChannel):
    """Benachrichtigungen via Web Push API (Service Worker).

    Erfordert: VAPID-Key-Paar, Service Worker im Frontend,
    PushSubscription in notification_preferences gespeichert.
    """

    channel_key = "pwa"
    supports_actions = True   # Web Push unterstuetzt Actions
    supports_batching = False

    async def send(
        self,
        notification: Notification,
        channel_config: dict,
    ) -> ChannelResult:
        subscription = channel_config.get("push_subscription")
        if not subscription:
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error="No push subscription registered",
            )

        # pywebpush.webpush() mit VAPID-Credentials
        ...
```

### 3.6 Apprise Channel (Optional)

```python
class AppriseNotificationChannel(INotificationChannel):
    """Benachrichtigungen via Apprise (100+ Dienste).

    Apprise ist ein Python-Paket das eine einheitliche API fuer
    Telegram, Slack, Pushover, Gotify, ntfy, Discord, Matrix,
    XMPP, Webhook, und 100+ weitere Dienste bietet.

    Konfiguration: Der Nutzer hinterlegt eine oder mehrere
    Apprise-URLs in seinen Notification Preferences:
    - tgram://bottoken/chatid (Telegram)
    - slack://tokenA/tokenB/channel (Slack)
    - gotify://hostname/token (Gotify)
    - ntfy://topic (ntfy)
    - pover://user@token (Pushover)

    Abhaengigkeit: `pip install apprise` (optional dependency)
    """

    channel_key = "apprise"
    supports_actions = False
    supports_batching = True

    async def send(
        self,
        notification: Notification,
        channel_config: dict,
    ) -> ChannelResult:
        urls = channel_config.get("urls", [])
        if not urls:
            return ChannelResult(
                channel_key=self.channel_key,
                success=False,
                error="No Apprise URLs configured",
            )

        import apprise

        apobj = apprise.Apprise()
        for url in urls:
            apobj.add(url)

        notify_type = {
            NotificationUrgency.LOW: apprise.NotifyType.INFO,
            NotificationUrgency.NORMAL: apprise.NotifyType.INFO,
            NotificationUrgency.HIGH: apprise.NotifyType.WARNING,
            NotificationUrgency.CRITICAL: apprise.NotifyType.FAILURE,
        }[notification.urgency]

        success = await apobj.async_notify(
            title=notification.title,
            body=notification.body,
            notify_type=notify_type,
        )

        return ChannelResult(
            channel_key=self.channel_key,
            success=success,
        )
```

### 3.7 Notification Channel Registry

```python
from typing import ClassVar


class NotificationChannelRegistry:
    """Registry fuer Benachrichtigungskanaele."""

    _channels: ClassVar[dict[str, type[INotificationChannel]]] = {}

    @classmethod
    def register(cls, channel_cls: type[INotificationChannel]) -> type[INotificationChannel]:
        cls._channels[channel_cls.channel_key] = channel_cls
        return channel_cls

    @classmethod
    def get(cls, channel_key: str) -> INotificationChannel:
        channel_cls = cls._channels.get(channel_key)
        if not channel_cls:
            raise KeyError(f"Unknown channel '{channel_key}'. Available: {list(cls._channels.keys())}")
        return channel_cls()

    @classmethod
    def all_keys(cls) -> list[str]:
        return list(cls._channels.keys())
```

### 3.8 Notification Engine

```python
from datetime import datetime, timezone

import structlog

logger = structlog.get_logger()


class NotificationEngine:
    """Orchestriert die Benachrichtigungszustellung.

    Verantwortlich fuer:
    - Routing: Welche Kanaele bekommt welcher Nutzer?
    - Batching: Mehrere Notifications zusammenfassen
    - Quiet Hours: Zeitfenster beachten
    - Eskalation: Ueberfaellige Re-Notification
    - Dedup: Keine doppelten Notifications (Redis)
    - Fallback: Wenn primaerer Kanal fehlschlaegt → naechster Kanal
    """

    def __init__(
        self,
        notification_repo,
        preference_repo,
        channel_registry: NotificationChannelRegistry,
        redis_client,
    ) -> None:
        self._notif_repo = notification_repo
        self._pref_repo = preference_repo
        self._registry = channel_registry
        self._redis = redis_client

    async def notify(
        self,
        user_key: str,
        tenant_key: str,
        notification: Notification,
    ) -> dict:
        """Sendet eine Notification an einen Nutzer ueber seine konfigurierten Kanaele."""

        # Dedup-Check (Redis, TTL 24h)
        dedup_key = f"notif:dedup:{user_key}:{notification.notification_type}:{notification.group_key}"
        if await self._redis.exists(dedup_key):
            logger.debug("notification_deduped", key=dedup_key)
            return {"status": "deduped"}

        # Preferences laden
        prefs = await self._pref_repo.get_by_user(user_key)
        if not prefs:
            prefs = self._default_preferences()

        # Quiet Hours pruefen
        if self._is_quiet_hours(prefs) and not self._ignores_quiet_hours(notification, prefs):
            # In Queue fuer naechsten Morning-Dispatch einreihen
            await self._enqueue_for_morning(user_key, tenant_key, notification, prefs)
            return {"status": "queued_quiet_hours"}

        # Kanaele bestimmen (Type-Override oder Default-Kanaele)
        channel_keys = self._resolve_channels(notification, prefs)

        # Senden (in Prio-Reihenfolge, mit Fallback)
        channels_sent = []
        channels_failed = []

        for channel_key in channel_keys:
            try:
                channel = self._registry.get(channel_key)
                channel_config = prefs["channels"].get(channel_key, {}).get("config", {})
                result = await channel.send(notification, channel_config)

                if result.success:
                    channels_sent.append(channel_key)
                else:
                    channels_failed.append(channel_key)
                    logger.warning(
                        "channel_failed",
                        channel=channel_key,
                        error=result.error,
                    )
            except KeyError:
                logger.warning("channel_not_registered", channel=channel_key)
                channels_failed.append(channel_key)

        # Notification persistieren
        doc = {
            "tenant_key": tenant_key,
            "user_key": user_key,
            "notification_type": notification.notification_type,
            "title": notification.title,
            "body": notification.body,
            "urgency": notification.urgency.value,
            "data": notification.data,
            "channels_sent": channels_sent,
            "channels_failed": channels_failed,
            "ha_event_type": notification.ha_event_type,
            "status": "delivered" if channels_sent else "failed",
            "escalation_level": 0,
            "created_at": datetime.now(tz=timezone.utc).isoformat(),
        }
        saved = await self._notif_repo.create(doc)

        # Dedup-Key setzen (24h TTL)
        await self._redis.setex(dedup_key, 86400, saved["_key"])

        return {
            "status": "delivered" if channels_sent else "failed",
            "notification_key": saved["_key"],
            "channels_sent": channels_sent,
            "channels_failed": channels_failed,
        }

    async def notify_batch(
        self,
        user_key: str,
        tenant_key: str,
        notifications: list[Notification],
    ) -> dict:
        """Sendet mehrere Notifications als Batch (wenn Kanal Batching unterstuetzt)."""
        prefs = await self._pref_repo.get_by_user(user_key)
        if not prefs:
            prefs = self._default_preferences()

        channel_keys = self._resolve_channels(notifications[0], prefs)

        for channel_key in channel_keys:
            try:
                channel = self._registry.get(channel_key)
                channel_config = prefs["channels"].get(channel_key, {}).get("config", {})

                if channel.supports_batching:
                    await channel.send_batch(notifications, channel_config)
                else:
                    for n in notifications:
                        await channel.send(n, channel_config)
            except Exception as exc:
                logger.warning("batch_channel_failed", channel=channel_key, error=str(exc))

        return {"status": "delivered", "count": len(notifications)}

    async def escalate_overdue(self, tenant_key: str) -> dict:
        """Prueft ueberfaellige Notifications und eskaliert.

        Wird taeglich via Celery aufgerufen.
        Nur fuer care.watering mit aktivierter Eskalation.
        """
        overdue = await self._notif_repo.find_overdue_watering(tenant_key)
        escalated = 0

        for notif in overdue:
            days_overdue = (datetime.now(tz=timezone.utc) - notif["created_at"]).days
            current_level = notif.get("escalation_level", 0)
            prefs = await self._pref_repo.get_by_user(notif["user_key"])
            escalation_days = (prefs or {}).get("escalation", {}).get("escalation_days", [2, 4, 7])

            next_level = None
            for i, day in enumerate(escalation_days):
                if days_overdue >= day and current_level <= i:
                    next_level = i + 1

            if next_level is not None and next_level <= len(escalation_days):
                urgency = [
                    NotificationUrgency.HIGH,
                    NotificationUrgency.CRITICAL,
                    NotificationUrgency.CRITICAL,
                ][min(next_level - 1, 2)]

                escalated_notif = Notification(
                    notification_key=f"{notif['_key']}_esc{next_level}",
                    notification_type="care.watering",
                    title=f"UEBERFAELLIG: {notif['title']}",
                    body=f"{notif['body']} (seit {days_overdue} Tagen ueberfaellig!)",
                    urgency=urgency,
                    data=notif.get("data", {}),
                    ha_event_type="kamerplanter_care_due",
                    actions=[
                        NotificationAction(
                            action_id="confirm_watering",
                            title="Jetzt erledigt",
                            uri="/pflege",
                        ),
                    ],
                )

                await self.notify(notif["user_key"], tenant_key, escalated_notif)
                await self._notif_repo.update(
                    notif["_key"],
                    {"escalation_level": next_level},
                )
                escalated += 1

        return {"escalated": escalated}

    def _resolve_channels(self, notification: Notification, prefs: dict) -> list[str]:
        """Bestimmt die Zustellkanaele basierend auf Type-Overrides und Default-Prio."""
        type_override = prefs.get("type_overrides", {}).get(notification.notification_type)
        if type_override:
            return type_override["channels"]

        # Default: Alle aktiven Kanaele in Prio-Reihenfolge
        active = [
            (k, v.get("priority", 99))
            for k, v in prefs.get("channels", {}).items()
            if v.get("enabled", False)
        ]
        active.sort(key=lambda x: x[1])
        return [k for k, _ in active]

    def _is_quiet_hours(self, prefs: dict) -> bool:
        """Prueft ob aktuell Quiet Hours gelten."""
        qh = prefs.get("quiet_hours", {})
        if not qh.get("enabled", False):
            return False
        # Zeitzone-aware Check gegen start/end
        ...
        return False

    def _ignores_quiet_hours(self, notification: Notification, prefs: dict) -> bool:
        """Bestimmte Typen ignorieren Quiet Hours (Frostwarnung, Sensor-Alarm)."""
        type_override = prefs.get("type_overrides", {}).get(notification.notification_type, {})
        return type_override.get("ignore_quiet_hours", False)

    @staticmethod
    def _default_preferences() -> dict:
        """Standard-Preferences fuer Nutzer ohne Konfiguration."""
        return {
            "channels": {
                "home_assistant": {"enabled": False, "priority": 1, "config": {}},
                "email": {"enabled": False, "priority": 2, "config": {}},
            },
            "quiet_hours": {"enabled": True, "start": "22:00", "end": "07:00"},
            "batching": {"enabled": True, "window_minutes": 30},
            "escalation": {"watering_enabled": True, "escalation_days": [2, 4, 7]},
            "type_overrides": {},
        }
```

### 3.9 Celery-Tasks

```python
from celery import shared_task


@shared_task(name="notifications.dispatch_due_care")
def dispatch_due_care_notifications() -> dict:
    """Versendet Benachrichtigungen fuer faellige Pflegeaufgaben.

    Laeuft taeglich nach generate_due_care_reminders (REQ-022).
    Celery Beat: 06:05 UTC (5 Minuten nach REQ-022 Task-Generierung).

    Logik:
    1. Lade alle heute faelligen Tasks mit category='care_reminder'
    2. Gruppiere nach User + Notification-Type
    3. Sende Batched Notifications via NotificationEngine
    """
    ...


@shared_task(name="notifications.escalate_overdue")
def escalate_overdue_notifications() -> dict:
    """Prueft und eskaliert ueberfaellige Giess-Erinnerungen.

    Laeuft taeglich um 12:00 UTC (Mittags-Check).
    """
    ...


@shared_task(name="notifications.send_daily_summary")
def send_daily_summary() -> dict:
    """Sendet die taegliche Pflege-Zusammenfassung.

    Laeuft taeglich zur konfigurierten Zeit (Default 07:00 Nutzer-Zeitzone).
    Sammelt: Faellige Tasks + Ueberfallige + Wetter-Hinweise + Saisonale.
    """
    ...


@shared_task(name="notifications.send_email_digests")
def send_email_digests() -> dict:
    """Versendet gesammelte E-Mail-Digests.

    Laeuft taeglich zur konfigurierten Digest-Zeit.
    """
    ...
```

### 3.10 Celery Beat Schedule

```python
CELERY_BEAT_SCHEDULE = {
    # ... bestehende Tasks ...

    # REQ-030: Notifications
    "notifications-dispatch-care-daily": {
        "task": "notifications.dispatch_due_care",
        "schedule": crontab(hour=6, minute=5),
    },
    "notifications-escalate-overdue": {
        "task": "notifications.escalate_overdue",
        "schedule": crontab(hour=12, minute=0),
    },
    "notifications-daily-summary": {
        "task": "notifications.send_daily_summary",
        "schedule": crontab(hour=6, minute=30),
    },
    "notifications-email-digests": {
        "task": "notifications.send_email_digests",
        "schedule": crontab(hour=7, minute=0),
    },
}
```

### 3.11 REST-API Endpunkte

```python
from fastapi import APIRouter, Depends

router = APIRouter(
    prefix="/api/v1/t/{tenant_slug}/notifications",
    tags=["notifications"],
)


@router.get("/")
async def list_notifications(
    tenant_slug: str,
    limit: int = Query(50, ge=1, le=200),
    unread_only: bool = Query(False),
    user=Depends(get_current_user),
) -> list[dict]:
    """Liste der Benachrichtigungen eines Nutzers."""
    ...


@router.post("/{notification_key}/read")
async def mark_read(
    tenant_slug: str,
    notification_key: str,
    user=Depends(get_current_user),
) -> dict:
    """Markiert eine Notification als gelesen."""
    ...


@router.post("/{notification_key}/act")
async def mark_acted(
    tenant_slug: str,
    notification_key: str,
    action_id: str = Query(...),
    user=Depends(get_current_user),
) -> dict:
    """Markiert eine Notification als bearbeitet (Actionable Button).

    action_id: z.B. 'confirm_watering' → loest CareConfirmation aus (REQ-022)
    """
    ...


@router.get("/preferences")
async def get_preferences(
    tenant_slug: str,
    user=Depends(get_current_user),
) -> dict:
    """Benachrichtigungs-Einstellungen des Nutzers."""
    ...


@router.put("/preferences")
async def update_preferences(
    tenant_slug: str,
    preferences: dict,
    user=Depends(get_current_user),
) -> dict:
    """Aktualisiert Benachrichtigungs-Einstellungen."""
    ...


@router.get("/channels/status")
async def channel_status(
    tenant_slug: str,
    user=Depends(get_current_user),
) -> dict:
    """Status aller Benachrichtigungskanaele (verfuegbar? konfiguriert? gesund?)."""
    ...


@router.post("/test")
async def send_test_notification(
    tenant_slug: str,
    channel_key: str = Query(...),
    user=Depends(get_current_user),
) -> dict:
    """Sendet eine Test-Notification ueber einen bestimmten Kanal."""
    ...
```

## 4. Home Assistant Custom Integration Erweiterung

### 4.1 Neue HA Event-Typen

```python
# Ergaenzung in const.py
EVENT_CARE_DUE: Final = f"{DOMAIN}_care_due"
EVENT_SEASONAL: Final = f"{DOMAIN}_seasonal"
EVENT_SENSOR_ALERT: Final = f"{DOMAIN}_sensor_alert"
EVENT_IPM_ALERT: Final = f"{DOMAIN}_ipm_alert"
EVENT_TANK_ALERT: Final = f"{DOMAIN}_tank_alert"
EVENT_HARVEST: Final = f"{DOMAIN}_harvest"
EVENT_TASK_DUE: Final = f"{DOMAIN}_task_due"
EVENT_WEATHER_ALERT: Final = f"{DOMAIN}_weather_alert"
EVENT_PHASE: Final = f"{DOMAIN}_phase"
```

### 4.2 Neue HA Platform: `notify`

Die Kamerplanter HA-Integration registriert einen **Notify-Service**, ueber den HA-Automationen Kamerplanter-Aktionen bestaetigen koennen:

```python
# notify.py (neue Platform in der HA-Integration)

class KamerplanterNotifyService(BaseNotificationService):
    """Empfaengt Actionable Notification Responses von der HA Companion App.

    Wenn der Nutzer in der HA-Notification auf 'Erledigt' tippt,
    sendet die Companion App ein Event. Diese Platform faengt es ab
    und ruft den Kamerplanter-Backend-Endpunkt auf, um die
    CareConfirmation (REQ-022) zu erstellen.
    """

    async def async_send_message(self, message: str, **kwargs) -> None:
        """Handle action callback from Companion App."""
        data = kwargs.get("data", {})
        action_id = data.get("action_id")
        notification_key = data.get("notification_key")

        if action_id == "confirm_watering":
            await self._api.async_confirm_care_reminder(
                notification_key=notification_key,
                action="confirmed",
            )
            # Persistent Notification entfernen
            await self.hass.services.async_call(
                "persistent_notification", "dismiss",
                {"notification_id": f"kp_{notification_key}"},
            )
```

### 4.3 Automation Blueprints

Die HA-Integration liefert vorgefertigte **Automation Blueprints** mit:

**Blueprint 1: Pflegeerinnerung an Companion App weiterleiten**
```yaml
# blueprints/automation/kamerplanter/care_notification.yaml
blueprint:
  name: "Kamerplanter: Pflegeerinnerung an Handy senden"
  description: >-
    Leitet Kamerplanter-Pflegeerinnerungen als Push-Notification
    an die Home Assistant Companion App weiter.
  domain: automation
  input:
    notify_service:
      name: Benachrichtigungsdienst
      description: "Welches Geraet soll benachrichtigt werden?"
      selector:
        target:
          entity:
            domain: notify
    urgency_filter:
      name: Mindest-Dringlichkeit
      description: "Nur Notifications ab dieser Dringlichkeit weiterleiten"
      default: "normal"
      selector:
        select:
          options:
            - "low"
            - "normal"
            - "high"
            - "critical"

trigger:
  - platform: event
    event_type: kamerplanter_care_due

condition:
  - condition: template
    value_template: >-
      {{ trigger.event.data.urgency in ['normal', 'high', 'critical']
         if states('input_select.kp_urgency_filter') == 'normal'
         else trigger.event.data.urgency in ['high', 'critical'] }}

action:
  - service: "{{ notify_service }}"
    data:
      title: "{{ trigger.event.data.title }}"
      message: "{{ trigger.event.data.body }}"
      data:
        actions:
          - action: "CONFIRM_KP_{{ trigger.event.data.notification_key }}"
            title: "Erledigt"
          - action: "SNOOZE_KP_{{ trigger.event.data.notification_key }}"
            title: "Spaeter"
        tag: "kp_{{ trigger.event.data.notification_key }}"
        group: "kamerplanter"
        importance: >-
          {{ 'high' if trigger.event.data.urgency in ['high', 'critical'] else 'default' }}
```

**Blueprint 2: Frostwarnung → Gewaechshausheizung einschalten**
```yaml
blueprint:
  name: "Kamerplanter: Frostwarnung → Heizung aktivieren"
  description: >-
    Schaltet bei einer Kamerplanter-Frostwarnung automatisch
    die Gewaechshausheizung ein.
  domain: automation
  input:
    heater_entity:
      name: Heizung
      selector:
        entity:
          domain: [switch, climate]
    target_temp:
      name: Zieltemperatur
      default: 5
      selector:
        number:
          min: 2
          max: 15

trigger:
  - platform: event
    event_type: kamerplanter_weather_alert
    event_data:
      type: "weather.frost"

action:
  - choose:
      - conditions:
          - condition: template
            value_template: "{{ states[heater_entity].domain == 'climate' }}"
        sequence:
          - service: climate.set_temperature
            target:
              entity_id: "{{ heater_entity }}"
            data:
              temperature: "{{ target_temp }}"
      - conditions:
          - condition: template
            value_template: "{{ states[heater_entity].domain == 'switch' }}"
        sequence:
          - service: switch.turn_on
            target:
              entity_id: "{{ heater_entity }}"
```

**Blueprint 3: Morgendliche TTS-Zusammenfassung**
```yaml
blueprint:
  name: "Kamerplanter: Morgendliche Pflegeansage"
  description: >-
    Spricht morgens eine Zusammenfassung der faelligen Pflegeaufgaben
    ueber einen smarten Lautsprecher.
  domain: automation
  input:
    tts_entity:
      name: Lautsprecher
      selector:
        entity:
          domain: media_player
    trigger_time:
      name: Uhrzeit
      default: "07:30:00"
      selector:
        time:

trigger:
  - platform: time
    at: !input trigger_time

condition:
  - condition: state
    entity_id: sensor.kp_tasks_due_today
    state: "> 0"

action:
  - service: tts.speak
    target:
      entity_id: !input tts_entity
    data:
      message: >-
        Guten Morgen! Heute stehen {{ states('sensor.kp_tasks_due_today') }}
        Pflegeaufgaben an.
        {{ state_attr('sensor.kp_tasks_due_today', 'summary') }}
```

### 4.4 Neue HA Sensor-Entities

| Entity | Typ | Beschreibung |
|--------|-----|-------------|
| `sensor.kp_tasks_due_today` | Sensor | Anzahl faelliger Tasks heute |
| `sensor.kp_tasks_overdue` | Sensor | Anzahl ueberfaelliger Tasks |
| `sensor.kp_next_watering` | Sensor | Naechste faellige Pflanze + Zeitpunkt |
| `binary_sensor.kp_care_overdue` | Binary Sensor | True wenn mindestens 1 Task ueberfaellig |

Attribute auf `sensor.kp_tasks_due_today`:
- `summary`: Text-Zusammenfassung ("Monstera giessen, Ficus duengen")
- `plants`: Liste der betroffenen Pflanzen mit Details
- `urgency_counts`: `{"overdue": 2, "due_today": 3, "upcoming": 5}`

### 4.5 Custom Lovelace Card: Pflege-Dashboard

```javascript
// www/kamerplanter-care-card.js
// MUI-inspirierte Karte fuer das HA Dashboard

class KamerplanterCareCard extends HTMLElement {
  /* Zeigt:
   * - Ueberfaellige Aufgaben (rot, oben)
   * - Heute faellig (orange)
   * - Kommende 3 Tage (grau)
   *
   * Jede Zeile: Pflanzenname + Icon + Aufgabentyp + "Erledigt"-Button
   * Erledigt-Button ruft kamerplanter.confirm_care Service auf
   */
}
```

## 5. Frontend-Integration

### 5.1 Notification-Einstellungen (Neue Seite)

**Route:** `/einstellungen/benachrichtigungen`

**Tab in AccountSettingsPage** (erweitert bestehende 5 Tabs um Tab 6: "Benachrichtigungen"):

| Sektion | Inhalt |
|---------|--------|
| **Kanaele** | Toggle pro Kanal (HA, E-Mail, PWA, Apprise). HA-Kanal zeigt Verbindungsstatus. E-Mail-Feld fuer Adresse. Apprise-URLs als Textarea. |
| **Zeitplan** | Quiet Hours (Start/Ende), Daily Summary (Zeit + Kanal) |
| **Batching** | Toggle + Zeitfenster (Default 30 Min) |
| **Eskalation** | Toggle fuer Giess-Eskalation + Tage-Konfiguration |
| **Typ-Overrides** | Pro Notification-Typ: Kanal-Auswahl, Quiet-Hours-Override |
| **Test** | "Test-Notification senden"-Button pro Kanal |

### 5.2 In-App Notification Center

**Bell-Icon in der AppBar** mit Badge (ungelesene Count):
- Dropdown/Drawer mit Notification-Liste
- Swipe-to-dismiss oder "Alle gelesen"-Button
- Klick auf Notification navigiert zur relevanten Seite

### 5.3 Erfahrungsstufen-Integration (REQ-021)

| Element | Beginner | Intermediate | Expert |
|---------|----------|-------------|--------|
| Kanal-Konfiguration | Nur HA + E-Mail | Alle Kanaele | Alle + Apprise-URLs |
| Quiet Hours | Default (22-07) | Konfigurierbar | Konfigurierbar |
| Eskalation | Default (an) | Konfigurierbar | Konfigurierbar + Tage |
| Typ-Overrides | Ausgeblendet | Vereinfacht | Vollstaendig |
| Test-Button | Sichtbar | Sichtbar | Sichtbar + Response-Details |

## 6. Konfiguration & Deployment

### 6.1 Settings (Ergaenzung)

```python
class Settings(BaseSettings):
    # REQ-030: Notifications
    ha_url: str | None = None                # Home Assistant URL
    ha_token: str | None = None              # HA Long-Lived Access Token
    vapid_private_key: str | None = None     # VAPID fuer PWA Push
    vapid_public_key: str | None = None
    vapid_contact_email: str | None = None
    notification_quiet_hours_default: str = "22:00-07:00"
    notification_batch_window_minutes: int = 30
    notification_escalation_days: str = "2,4,7"
```

### 6.2 Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: kamerplanter-notifications
type: Opaque
stringData:
  HA_URL: "http://homeassistant.local:8123"   # Optional
  HA_TOKEN: "your-ha-long-lived-access-token"  # Optional
  VAPID_PRIVATE_KEY: "..."                     # Optional (fuer PWA Push)
  VAPID_PUBLIC_KEY: "..."
```

### 6.3 Feature-Toggle-Logik

```
HA_URL + HA_TOKEN gesetzt?
  ├── Ja → HomeAssistantChannel aktiv (Events, Persistent, Push, TTS)
  └── Nein → HA-Kanal deaktiviert

SMTP konfiguriert (bestehend aus REQ-023)?
  ├── Ja → EmailChannel aktiv
  └── Nein → E-Mail-Kanal deaktiviert

VAPID Keys gesetzt?
  ├── Ja → PwaChannel aktiv
  └── Nein → PWA-Push deaktiviert

Apprise installiert + URLs konfiguriert?
  ├── Ja → AppriseChannel aktiv
  └── Nein → Apprise deaktiviert

Kein Kanal aktiv?
  └── InApp-Notifications als Fallback (Pflege-Dashboard REQ-022)
```

## 7. Authentifizierung & Autorisierung

| Endpoint | Auth | Bemerkung |
|----------|------|-----------|
| `GET /notifications` | JWT + Tenant | Nur eigene Notifications |
| `POST /{key}/read` | JWT + Tenant | Nur eigene |
| `POST /{key}/act` | JWT + Tenant | Loest CareConfirmation aus |
| `GET /preferences` | JWT + Tenant | Nur eigene |
| `PUT /preferences` | JWT + Tenant | Nur eigene |
| `GET /channels/status` | JWT + Tenant | — |
| `POST /test` | JWT + Tenant | Rate-Limited (5/Stunde) |

**HA → Backend Kommunikation:**
Die HA-Integration nutzt den bestehenden **Service Account** (REQ-023 v1.7) oder **API-Key** fuer Rueckkanal-Calls (Actionable Button Callbacks → CareConfirmation).

## 8. Abhaengigkeiten

**Benoetigt:**
- **REQ-022** v2.4 (Pflegeerinnerungen) — Celery-Tasks als Notification-Quelle
- **REQ-006** v2.7 (Aufgabenplanung) — Task-System als Notification-Quelle
- **REQ-023** v1.7 (Auth) — JWT + Service Accounts fuer HA-Rueckkanal
- **REQ-024** v1.3 (Mandantenverwaltung) — Tenant-Scoping

**Stark integriert:**
- **REQ-018** v1.0 (Umgebungssteuerung) — HA-Client wird erweitert, Sensor/Aktor-Alerts als Notifications
- **REQ-005** (Sensorik) — Sensor-Alarme als Notification-Quelle
- **REQ-010** v1.0 (IPM) — IPM-Alerts als Notification-Quelle
- **REQ-014** v1.4 (Tankmanagement) — Tank-Alarme als Notification-Quelle

**Optional (Synergie):**
- **REQ-007** v1.0 (Ernte) — Ernte-Bereitschafts-Notifications
- **REQ-003** (Phasen) — Phasen-Transitions als Notifications
- **REQ-029** (Bilderkennung) — Krankheitsdiagnose-Ergebnis als Notification

**Systemabhaengigkeiten:**
- ArangoDB (Notification + Preference Persistenz)
- Redis (Dedup, Rate-Limiting, Batching-Queue, Quiet-Hours-Queue)
- Celery (Scheduled Dispatch, Eskalation, Daily Summary, Email Digest)
- httpx (HA REST API Calls)
- Pillow (optional, fuer Notification-Bilder)

**Optionale Abhaengigkeiten:**
- `apprise` (pip install apprise) — Fuer Apprise-Kanal
- `pywebpush` (pip install pywebpush) — Fuer PWA Push
- Home Assistant Instanz mit Long-Lived Access Token

**Wird benoetigt von:**
- Keine bestehende REQ haengt von REQ-030 ab

## 9. Akzeptanzkriterien

### Definition of Done (DoD):

- [ ] **INotificationChannel Interface** implementiert
- [ ] **HomeAssistantChannel:** Events, Persistent Notifications, Mobile Push, TTS
- [ ] **EmailChannel:** Einzel-Mail und Daily Digest
- [ ] **PwaChannel:** Web Push via Service Worker + VAPID
- [ ] **AppriseChannel:** 100+ Dienste via Apprise-URLs
- [ ] **InAppChannel:** Fallback wenn kein externer Kanal aktiv
- [ ] **NotificationEngine:** Routing, Batching, Quiet Hours, Dedup, Eskalation
- [ ] **Celery Tasks:** dispatch_due_care (06:05), escalate_overdue (12:00), daily_summary (06:30), email_digests (07:00)
- [ ] **HA Client Erweiterung:** fire_event, create_persistent_notification, call_service, dismiss
- [ ] **HA Custom Integration:** Neue Event-Typen, Sensor-Entities (tasks_due_today, tasks_overdue, next_watering, care_overdue)
- [ ] **HA Automation Blueprints:** Care Push, Frostwarnung→Heizung, TTS-Zusammenfassung
- [ ] **HA Lovelace Card:** kamerplanter-care-card mit Erledigt-Button
- [ ] **Frontend:** Notification-Tab in Einstellungen, Bell-Icon mit Badge, In-App Notification Center
- [ ] **REST-Endpunkte:** list, read, act, preferences, channel-status, test
- [ ] **i18n:** Alle Texte in DE und EN
- [ ] **Feature-Toggles:** Jeder Kanal unabhaengig aktivierbar, App funktioniert ohne jeden Kanal
- [ ] **Testabdeckung:** Unit-Tests fuer alle Channels (gemockt), Engine, Celery Tasks

### Testszenarien:

**Szenario 1: HA Push — Giess-Erinnerung mit Actionable Button**
```
GIVEN: Nutzer hat HA-Kanal aktiviert mit mobile_push=true und actionable_buttons=true
  AND: REQ-022 hat 3 faellige Giess-Tasks generiert
WHEN: Celery dispatch_due_care laeuft um 06:05
THEN:
  - HA Event 'kamerplanter_care_due' wird gefeuert
  - Persistent Notification im HA-Frontend erscheint
  - Mobile Push auf Companion App: "3 Pflanzen giessen heute"
    mit Buttons "Erledigt" und "Spaeter"
  - Nutzer tippt "Erledigt" → CareConfirmation wird erstellt (REQ-022)
  - Persistent Notification wird entfernt
```

**Szenario 2: HA TTS — Morgendliche Ansage**
```
GIVEN: Nutzer hat tts_enabled=true, tts_entity_id="media_player.kueche"
  AND: Daily Summary um 07:00 konfiguriert
WHEN: Celery daily_summary laeuft
THEN:
  - HA Service tts.speak wird aufgerufen
  - Lautsprecher sagt: "Guten Morgen! Heute stehen 5 Pflegeaufgaben an:
    Monstera, Ficus und Basilikum giessen. Calathea Schaedlingskontrolle.
    Orchidee umtopfen."
```

**Szenario 3: Eskalation — Vergessene Giess-Erinnerung**
```
GIVEN: Giess-Erinnerung fuer Monstera am 19.03. gesendet, nicht bestaetigt
WHEN: Celery escalate_overdue laeuft am 21.03. (Tag +2)
THEN:
  - Neue Notification: "UEBERFAELLIG: Monstera giessen (seit 2 Tagen!)"
  - Dringlichkeit: HIGH
  - HA Event mit urgency=high
WHEN: Immer noch nicht bestaetigt am 23.03. (Tag +4)
THEN:
  - Erneute Notification: Dringlichkeit CRITICAL
WHEN: Immer noch nicht bestaetigt am 26.03. (Tag +7)
THEN:
  - Letzte Warnung, danach keine weiteren Eskalationen
```

**Szenario 4: Frostwarnung → HA Automation**
```
GIVEN: REQ-005 Wetter-Integration erkennt Frost fuer morgen Nacht (-3°C)
  AND: HA Blueprint "Frostwarnung → Heizung" ist konfiguriert
WHEN: Kamerplanter sendet Event 'kamerplanter_weather_alert' mit type='weather.frost'
THEN:
  - HA Automation triggert
  - Gewaechshausheizung wird auf 5°C eingestellt
  - Nutzer erhaelt Push: "Frostwarnung morgen Nacht: -3°C erwartet"
  - Quiet Hours werden ignoriert (ignore_quiet_hours=true)
```

**Szenario 5: E-Mail Daily Digest**
```
GIVEN: Nutzer hat email.digest_mode="daily", email.digest_time="07:00"
  AND: 6 Notifications seit gestern gesammelt
WHEN: Celery email_digests laeuft um 07:00
THEN:
  - Eine zusammengefasste E-Mail wird gesendet
  - Betreff: "Kamerplanter: 6 Pflegeaufgaben heute"
  - Inhalt: Gruppiert nach Typ (Giessen, Duengen, etc.)
```

**Szenario 6: Quiet Hours**
```
GIVEN: Quiet Hours 22:00–07:00 konfiguriert
WHEN: Notification um 23:30 generiert wird (z.B. vorgezogene Celery-Task)
THEN:
  - Notification wird NICHT sofort gesendet
  - Eingereiht in Morning-Queue
  - Zustellung um 07:00 zusammen mit Daily Summary
ABER: sensor.alert mit ignore_quiet_hours=true wird sofort gesendet
```

**Szenario 7: Kein Kanal konfiguriert — Fallback**
```
GIVEN: Nutzer hat keine Kanaele aktiviert (weder HA noch E-Mail noch PWA)
WHEN: Pflegeerinnerung wird faellig
THEN:
  - InApp-Notification wird erstellt (notification in DB)
  - Bell-Icon im Frontend zeigt Badge
  - Pflege-Dashboard (REQ-022) zeigt Tasks wie bisher
  - Keine externe Zustellung — App funktioniert vollstaendig
```

**Szenario 8: HA Lovelace Care Card**
```
GIVEN: kamerplanter-care-card.js ist im HA Dashboard eingebunden
WHEN: Dashboard wird geoeffnet
THEN:
  - Karte zeigt:
    - 2 ueberfaellige Tasks (rot, oben)
    - 3 heute faellige Tasks (orange)
    - 5 kommende Tasks (grau)
  - Jede Zeile: Pflanzen-Icon + Name + Aufgabe + "Erledigt"-Button
  - Klick auf "Erledigt" → kamerplanter.confirm_care Service → Task bestaetigt
  - Karte aktualisiert sich automatisch (Coordinator Refresh)
```

**Szenario 9: Batching**
```
GIVEN: Batching aktiviert mit window_minutes=30
  AND: Um 06:05 werden 8 Giess-Erinnerungen generiert
WHEN: NotificationEngine verarbeitet die 8 Notifications
THEN:
  - Nicht 8 einzelne Pushes, sondern 1 Batch-Notification:
    "8 Pflanzen giessen heute: Monstera, Ficus, Basilikum, ..."
  - HA Event enthaelt alle 8 plant_keys
  - E-Mail enthaelt alle 8 in einer Mail
```

**Szenario 10: Apprise — Telegram**
```
GIVEN: Nutzer hat Apprise-URL "tgram://bottoken/chatid" konfiguriert
WHEN: Giess-Erinnerung wird faellig
THEN:
  - Apprise sendet Telegram-Nachricht an den konfigurierten Chat
  - Inhalt: "Kamerplanter: 3 Pflanzen giessen heute\n- Monstera\n- Ficus\n- Basilikum"
  - Dringlichkeit wird auf Telegram-Prioritaet gemappt
```

---

**Hinweise fuer RAG-Integration:**
- Keywords: Benachrichtigung, Notification, Push, Home Assistant, HA Events, TTS, Companion App, Actionable Notification, E-Mail Digest, Apprise, PWA Push, Eskalation, Quiet Hours, Batching
- Fachbegriffe: INotificationChannel, Adapter-Pattern, Dedup, Escalation, Persistent Notification, Automation Blueprint, Lovelace Card, VAPID, Service Worker
- Verknuepfung: Baut auf REQ-022 (Celery-Tasks) auf, nutzt REQ-018 (HA-Client), erweitert HA Custom Integration, synergiert mit REQ-005/REQ-010/REQ-014
