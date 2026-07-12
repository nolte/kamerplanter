# Betriebsmittel & Inventar (InvenTree)

Auf dieser Seite verwaltest du deine **Betriebsmittel** — Pumpen, Messgeräte, Werkzeuge, Beleuchtung, Filter und Reinigungsmittel — als eigenständige Objekte und kannst sie optional mit **InvenTree** verknüpfen, einer separaten, externen Inventarverwaltung. Die Verknüpfung erspart dir doppelte Pflege: Bestände und Verbrauch werden automatisch zwischen beiden Systemen abgeglichen. <!-- REQ-016 -->

!!! info "Optionale Integration"
    InvenTree ist keine Pflichtkomponente. Ohne InvenTree-Verbindung funktioniert Kamerplanter uneingeschränkt weiter — du kannst Betriebsmittel, Dünger und Tanks ganz normal verwalten, nur eben ohne automatischen Bestandsabgleich. Fällt eine bereits eingerichtete InvenTree-Instanz vorübergehend aus, blockiert das nirgends deine Arbeit in Kamerplanter (Graceful Degradation).

---

## Voraussetzungen

- Zugriff auf **Inventar → Betriebsmittel** in der Navigation — jedes Tenant-Mitglied kann Betriebsmittel ansehen, die Tenant-Rolle **Gärtner** oder **Admin** wird zum Anlegen und Bearbeiten benötigt, **Admin** zusätzlich zum Löschen
- Für die InvenTree-Verknüpfung zusätzlich: eine erreichbare InvenTree-Instanz mit einem gültigen API-Token sowie die Tenant-Rolle **Admin**, um die Verbindung einzurichten (siehe [Für technische Nutzer / Self-Hoster](#fuer-technische-nutzer-self-hoster))

---

## Was ist InvenTree?

[InvenTree](https://github.com/inventree/inventree) ist eine eigenständige, quelloffene Inventarverwaltung — ein separates System, das du zusätzlich zu Kamerplanter betreibst. Für die Verknüpfung sind drei Begriffe wichtig:

- **Part** — ein einzelner Artikel in InvenTree, z. B. "BioBizz Bio-Bloom 1L" oder "Bluelab pH Pen". Jeder Part hat eine eindeutige numerische ID.
- **Stock** (Bestand) — die aktuell in InvenTree hinterlegte Menge eines Parts, z. B. "12,5 Liter" oder "3 Stück".
- **Consumption Tracking** (Verbrauchstracking) — die automatische Rückmeldung von Verbrauch (z. B. verbrauchte Milliliter Dünger bei einer Düngung) als Bestandsbuchung an InvenTree.

Kamerplanter kann drei Arten eigener Objekte mit einem InvenTree-Part verknüpfen: **Dünger**, **Tanks** und **Betriebsmittel**. Zu jeder Verknüpfung merkt sich Kamerplanter zusätzlich den zuletzt aus InvenTree abgerufenen Bestand.

---

## Betriebsmittel verwalten

Betriebsmittel sind deine Ausrüstung, die weder Dünger noch Tank ist: Pumpen, pH-/EC-Messgeräte, Werkzeuge, Beleuchtung, Filter und Reinigungsmittel.

### Schritt 1: Zur Betriebsmittel-Übersicht navigieren

Klicke in der Navigation auf **Inventar → Betriebsmittel**.

### Schritt 2: Neues Betriebsmittel anlegen

Klicke auf **Betriebsmittel anlegen** und fülle das Formular aus:

| Feld | Beschreibung |
|------|-------------|
| Bezeichnung | Name des Betriebsmittels, z. B. "Bluelab pH Pen" |
| Typ | Werkzeug, Verbrauchsmaterial, Sensor / Messgerät, Beleuchtung, Pumpe, Filter, Behälter, Reinigungsmittel oder Sonstiges |
| Status | Aktiv, In Wartung, Eingelagert, Defekt oder Ausgemustert |
| Marke, Modell | Optional, für die eigene Übersicht |
| Seriennummer | Optional |
| Notizen | Freitext, z. B. Kalibrierhinweise |

### Schritt 3: Optional mit InvenTree verknüpfen

Im Abschnitt **InvenTree-Verknüpfung (optional)** trägst du die **InvenTree-Part-ID** ein — die numerische ID des passenden Parts in deiner InvenTree-Instanz.

!!! note "Teilweise verfügbar: InvenTree-Part-ID am Betriebsmittel"
    Das Eintragen der Part-ID hinterlegt die Kennung direkt am Betriebsmittel (sie erscheint als Chip in der Übersichtstabelle) — sie erzeugt für sich genommen aber noch keine synchronisierte Verknüpfung. Damit Bestand und Verbrauch tatsächlich automatisch mit InvenTree abgeglichen werden (Stock-Sync), muss zusätzlich eine Referenz über die API angelegt werden (siehe [Für technische Nutzer / Self-Hoster](#fuer-technische-nutzer-self-hoster)). Eine Part-Suche direkt in der Kamerplanter-Oberfläche ist geplant, aber noch nicht umgesetzt — die Part-ID findest du aktuell in deiner InvenTree-Instanz selbst.

### Bearbeiten und löschen

Über die Symbole in der Tabellenzeile bearbeitest oder löschst du ein Betriebsmittel. Zum Löschen benötigst du die Tenant-Rolle **Admin**; das Bearbeiten steht auch der Rolle **Gärtner** offen.

!!! info "Standort, Kaufdatum und Garantie sind noch nicht in der Oberfläche editierbar"
    Kamerplanter kann zu jedem Betriebsmittel auch einen zugeordneten Standort, ein Kaufdatum und ein Garantieende speichern — diese Felder lassen sich derzeit nur über die API setzen, nicht über das Anlage-/Bearbeiten-Formular.

---

## Bestandsstatus auf der Übersichtsseite

Oben auf der Betriebsmittel-Seite zeigt ein Banner, ob eine aktive InvenTree-Verbindung besteht:

- **„InvenTree-Verbindung … ist aktiv“** (grün, wenn der letzte Erreichbarkeitstest erfolgreich war) — Bestände werden automatisch synchronisiert.
- **„Keine InvenTree-Verbindung konfiguriert“** — Betriebsmittel lassen sich trotzdem ganz normal verwalten.

---

## Bestände synchronisieren (Stock-Sync)

Ist eine InvenTree-Verbindung aktiv und mindestens eine Verknüpfung (Referenz) angelegt, ruft Kamerplanter automatisch die aktuellen Bestandsmengen aus InvenTree ab:

- **Stock-Pull (Lesen):** stündlich, für alle verknüpften Dünger, Tanks und Betriebsmittel.
- **Verbrauchsmeldung (Schreiben):** alle 5 Minuten, für ausstehende Verbrauchsbuchungen.

Beide Läufe passieren im Hintergrund, ohne dass du etwas tun musst. Weicht der neu abgerufene Bestand um mehr als 20 % vom zuletzt bekannten Wert ab, protokolliert Kamerplanter das intern als Warnhinweis — praktisch, wenn jemand direkt in InvenTree größere Mengen entnommen oder nachbestellt hat.

---

## Verbrauch automatisch nachverfolgen (Consumption Tracking)

!!! note "Teilweise verfügbar: Automatische Verbrauchsmeldung"
    Der Mechanismus für automatische Verbrauchsbuchungen ist bereits vollständig angelegt: Eine Verknüpfung kann mit **Auto-Abzug** markiert werden, jede Buchung landet nachvollziehbar im unveränderlichen Transaktions-Log, und fehlgeschlagene Übertragungen werden bis zu dreimal automatisch wiederholt. Die automatische **Auslösung** dieser Buchungen bei einer Düngung oder einer Tank-Wartung ist jedoch noch nicht mit den entsprechenden Arbeitsabläufen verbunden — in dieser Version entstehen noch keine automatischen Buchungen, wenn du eine Düngung oder Wartung erfasst. Transaktions-Log und Übertragungsmechanismus lassen sich schon heute über die API nutzen, sobald Buchungen z. B. über ein eigenes Skript angelegt werden.

Ist eine Verknüpfung mit **Auto-Abzug** aktiviert, wird Kamerplanter künftig automatisch eine Bestandsbuchung ("Verbrauch") anlegen, sobald du:

- eine **Düngung** protokollierst (Menge des jeweils verwendeten Düngers), oder
- eine **Wartung** an einem Tank dokumentierst, bei der ein verknüpftes Verbrauchsmaterial (z. B. ein Reinigungsmittel) verwendet wurde.

Jede Buchung erhält den Status **ausstehend** und wird beim nächsten Übertragungslauf (spätestens nach 5 Minuten) an InvenTree gesendet. Schlägt eine Übertragung fehl, versucht Kamerplanter es bis zu dreimal erneut, bevor die Buchung als **fehlgeschlagen** markiert wird.

---

## Für technische Nutzer / Self-Hoster {#fuer-technische-nutzer-self-hoster}

Die InvenTree-Anbindung ist standardmäßig **deaktiviert** und muss vom Betreiber der Instanz freigeschaltet werden.

| Umgebungsvariable | Standard | Beschreibung |
|---|---|---|
| `INVENTREE_ENABLED` | `false` | Kill-Switch für die gesamte InvenTree-Integration. Ohne diese Variable liefern alle InvenTree-Endpunkte den Fehler „Funktion deaktiviert“ (HTTP 409) statt einer Serverstörung. |
| `INVENTREE_ALLOW_PRIVATE_ENDPOINT` | `false` | Erlaubt eine InvenTree-Instanz im lokalen Netzwerk oder Cluster (private/LAN-Adresse). Ohne diese Freigabe blockiert Kamerplanter aus Sicherheitsgründen (SSRF-Schutz) Verbindungen zu privaten Adressen — analog zu `HA_ALLOW_PRIVATE_ENDPOINT` bei der Home-Assistant-Anbindung. |

Ist die Integration aktiviert, richtest du Verbindung und Verknüpfungen über die REST-API ein — eine Oberfläche dafür gibt es noch nicht:

**1. Verbindung anlegen** (Tenant-Rolle Admin):

```
POST /inventree/connections
{
  "name": "Haupt-Inventar",
  "base_url": "https://inventree.example.com",
  "api_token": "<dein InvenTree-API-Token>",
  "verify_ssl": true
}
```

Der API-Token wird mit Fernet (AES-256) verschlüsselt gespeichert und nie im Klartext zurückgegeben — Antworten enthalten nur das Feld `api_token_set: true`. `POST /inventree/connections/{key}/health-check` prüft die Erreichbarkeit, ohne offenzulegen, ob ein Auth-Fehler oder eine falsche URL die Ursache ist.

**2. Passende InvenTree-Parts suchen** (jedes Tenant-Mitglied):

```
GET /inventree/browse/parts?query=BioBizz&limit=25
GET /inventree/browse/categories
```

**3. Eine Kamerplanter-Entität verknüpfen** (Tenant-Rolle Gärtner oder Admin):

```
POST /inventree/references/link
{
  "entity_collection": "fertilizers",
  "entity_key": "<Key des Düngers>",
  "inventree_part_id": 42,
  "auto_deduct": true,
  "deduct_unit": "ml"
}
```

`entity_collection` akzeptiert ausschließlich `fertilizers`, `tanks` oder `equipment` — jeder andere Wert wird mit HTTP 422 abgelehnt.

**4. Manuellen Sync auslösen:**

```
POST /inventree/sync/trigger
```

Löst außerhalb des stündlichen/5-Minuten-Rhythmus sofort einen kombinierten Stock-Pull und Verbrauchsmeldungs-Lauf aus.

**5. Transaktions-Log einsehen:**

```
GET /inventree/transactions?status=pending
```

Listet alle Bestandsbuchungen mit ihrem Status (`pending`, `synced`, `failed`).

!!! warning "Verbindungs-Verwaltung ist auf die Tenant-Rolle Admin beschränkt"
    Nur Mitglieder mit der Tenant-Rolle **Admin** dürfen InvenTree-Verbindungen anlegen, ändern oder löschen. Das Verknüpfen einzelner Dünger, Tanks oder Betriebsmittel sowie das Auslösen eines Syncs steht auch der Rolle **Gärtner** offen; das Löschen eines Betriebsmittels erfordert ebenfalls Admin.

---

## Häufige Fragen

??? question "Muss ich InvenTree nutzen, um Betriebsmittel zu verwalten?"
    Nein. Du kannst Betriebsmittel jederzeit ohne InvenTree-Verbindung anlegen, bearbeiten und löschen. Die InvenTree-Verknüpfung ist ein rein optionales Extra für den automatischen Bestandsabgleich.

??? question "Was passiert, wenn meine InvenTree-Instanz nicht erreichbar ist?"
    Kamerplanter blockiert dadurch nirgends deine Arbeit. Bereits erfasste Betriebsmittel, Dünger und Tanks bleiben vollständig nutzbar. Der Verbindungsstatus zeigt „nicht erreichbar“, und ausstehende Bestandsbuchungen warten, bis die Verbindung wiederhergestellt ist.

??? question "Wo finde ich die Part-ID in InvenTree?"
    Öffne den gewünschten Part in deiner InvenTree-Instanz — die ID steht in der URL-Adressleiste (z. B. `.../part/42/`) sowie meist direkt auf der Part-Detailseite.

??? question "Kann ich Dünger oder Tanks direkt in der Oberfläche mit InvenTree verknüpfen?"
    Aktuell noch nicht — dafür gibt es bislang nur die REST-API (siehe [Für technische Nutzer / Self-Hoster](#fuer-technische-nutzer-self-hoster)). Nur Betriebsmittel haben bereits ein Eingabefeld für die InvenTree-Part-ID in der Oberfläche.

---

## Siehe auch

- [Dünge-Logik](fertilization.md)
- [Tankmanagement](tanks.md)
- [Standorte & Substrate](locations-substrates.md)
- [Glossar: InvenTree](../reference/glossary.md#inventree)
- [Umgebungsvariablen: InvenTree-Integration](../reference/environment-variables.md#inventree-integration-req-016)
