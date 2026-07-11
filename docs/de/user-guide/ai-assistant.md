# KI-Assistent

!!! note "Teilweise verfügbar"
    Der KI-Assistent ist als eigene Seite **KI-Assistent** (`/ki-assistent`) nutzbar: Wissensfragen und ein kontextloser Chat funktionieren bereits. Die auf dieser Seite ebenfalls beschriebenen **Tipp-Karten**, der **Tipp des Tages** und die **„Warum?"-Buttons** sind als Bausteine im Frontend bereits gebaut, aber noch auf keiner Pflanzen-, Pflanzdurchlauf- oder Aufgabenseite eingebunden — sie erscheinen dort noch nirgends. Die folgenden zwei Abschnitte beschreiben den heutigen Stand im Präsens, die Abschnitte danach das **geplante Verhalten** im Futur. <!-- REQ-031 -->

Der KI-Assistent beantwortet Wissensfragen zur Pflanzenpflege auf Basis einer kuratierten Wissensbasis — klar als KI-generiert gekennzeichnet, mit Quellenangaben und ohne dass deine persönlichen Daten an ein Sprachmodell übertragen werden.

---

## Wissensfragen stellen

Öffne im Menü **KI-Assistent**. Trage deine Frage in das Textfeld ein — zum Beispiel „Was ist VPD und warum ist es wichtig?" — und klicke auf **Frage stellen** (oder sende mit Strg/Cmd + Enter). Die Antwort erscheint darunter, mit KI-Kennzeichnung und aufklappbaren Quellen.

Diese Wissensfragen sind **rein sachbezogen** — sie beziehen sich nicht auf deine konkreten Pflanzen, sondern auf allgemeines Pflanzenwissen aus der Wissensbasis. Deshalb ist dafür keine Einwilligung nötig, und die Funktion steht auch im anonymen [Light-Modus](light-mode.md) ohne Anmeldung zur Verfügung.

!!! example "Beispielfragen"
    - „Was ist VPD?"
    - „Wie senke ich den pH-Wert der Nährlösung?"
    - „Was bedeutet Karenzzeit?"

## Kontextbewusster Chat

Im Voll-Modus (angemeldet) öffnet die Schaltfläche **Chat öffnen** oben auf der Seite ein Chat-Fenster. Deine Nachricht wird Wort für Wort gestreamt beantwortet; jede Antwort erscheint in derselben KI-Hülle wie die Wissensfragen. Ein Abbrechen-Button stoppt eine laufende Antwort.

!!! warning "Aktivierung durch eine Administratorin oder einen Administrator nötig"
    Der Chat nutzt — anders als die reine Wissensfrage — den Kontext deines Gartens (Mandant) und erfordert deshalb zwei Freischaltungen, bevor er tatsächlich antwortet: Der Betreiber der Instanz muss KI-Funktionen aktiviert haben, **und** dein Garten (Mandant) muss KI-Funktionen zusätzlich freigeschaltet haben. Ist eine der beiden Stufen aus, erscheint beim Öffnen des Chats die Meldung „Die KI-Funktionen sind für diesen Garten aktuell deaktiviert." Es gibt aktuell noch keine Klickstrecke, mit der eine Administratorin oder ein Administrator diese Garten-Freischaltung selbst vornehmen kann — siehe [Für technische Nutzer / Self-Hoster](#fuer-technische-nutzer-self-hoster).

Fehlt zusätzlich deine Einwilligung, dass der Assistent Stammwerte deiner Pflanzen als Kontext nutzen darf, erscheint stattdessen der Hinweis „Für diese KI-Funktion fehlt deine Einwilligung …". Wie du diese Einwilligung erteilst, steht unter [Einwilligung erteilen](#einwilligung-erteilen).

---

## So ist der KI-Assistent aufgebaut (Drei-Stufen-Freischaltung)

Eine KI-Funktion antwortet nur, wenn alle relevanten Stufen zustimmen:

| Stufe | Wer entscheidet | Betrifft |
|-------|-----------------|----------|
| 1. Instanz-weit | Plattformbetreiber (Umgebungsvariable) | Alle KI-Funktionen der gesamten Instanz |
| 2. Garten (Mandant) | Administratorin/Administrator deines Gartens | Alle KI-Funktionen, die deinen Pflanzenkontext nutzen (Chat, künftig auch Tipp-Karten) |
| 3. Deine Einwilligung | Du selbst | Ob deine Pflanzendaten als Kontext gesendet werden dürfen, und ob ein Cloud-Provider statt eines lokalen Modells verwendet werden darf |

Reine Wissensfragen ohne Pflanzenbezug (siehe oben) benötigen nur Stufe 1 — sie funktionieren deshalb auch im Light-Modus ohne Login.

## Einwilligung erteilen {#einwilligung-erteilen}

Zwei Einwilligungen sind für den KI-Assistenten relevant:

| Einwilligung | Wofür nötig |
|--------------|-------------|
| KI-Zugriff auf deine Pflanzendaten | Für Chat, Tipp-Karten, Tipp des Tages und „Warum?"-Erklärungen — überall dort, wo die Antwort deinen konkreten Pflanzenkontext (Art, Phase, Substrat, EC-/pH-Werte) nutzt |
| KI-Verarbeitung über Cloud-Provider | Zusätzlich nur nötig, wenn deine Instanz einen Cloud-Provider (statt eines lokalen Modells) einsetzt |

Beide erscheinen im Bereich **Datenschutz** im Tab **Einwilligungen** und lassen sich dort aktuell nur einsehen, nicht per Klick erteilen oder widerrufen — das funktioniert bislang ausschließlich über die API. Details, Wortlaut der Einwilligungstexte und die genaue Klickstrecke stehen in [Datenschutz & DSGVO](privacy.md#einwilligungen-verwalten-art-7-dsgvo).

---

## Transparenz: Woran du eine KI-Antwort erkennst

Jede Antwort des KI-Assistenten trägt sichtbare Kennzeichnungen:

- **KI-Badge** („KI-generiert") — erscheint über jeder Antwort, mit Modell- und Provider-Name im Tooltip.
- **Quellen-Footer** — aufklappbare Liste der zitierten Wissensbasis-Einträge mit Relevanz-Wert und Sprache. Bei der Erfahrungsstufe Experte ist er standardmäßig aufgeklappt, sonst zugeklappt.
- **„Nutzt deine Pflanzendaten"-Indikator** — erscheint nur, wenn die Antwort auf Basis deines Pflanzenkontexts erzeugt wurde. Ein Klick darauf führt zu den Datenschutz-Einstellungen.
- **„Cloud-Verarbeitung"-Indikator** — erscheint nur, wenn die Antwort über einen externen Cloud-Provider statt lokal verarbeitet wurde.
- **„Allgemeine Information"-Hinweis** — erscheint, wenn deine Pflanze eine selbst angelegte Art/Sorte ist, zu der die Wissensbasis keine spezifischen Informationen hat; die Antwort bezieht sich dann auf die nächstliegende bekannte Gattung oder Familie.
- **Disclaimer** — unterhalb jeder Antwort: „KI-Antworten können fehlerhaft sein. Bei kritischen Entscheidungen bitte die Quellen prüfen."

!!! info "Cloud vs. lokal"
    Ob ein Cloud-Provider (z. B. Anthropic, OpenAI) oder ein lokal betriebenes Modell (Ollama) antwortet, legt der Plattformbetreiber fest. Lokale Provider senden keine Daten nach außen und benötigen keine gesonderte Einwilligung; Cloud-Provider erfordern zusätzlich deine Einwilligung zur „KI-Verarbeitung über Cloud-Provider" (siehe oben).

## Datensparsamkeit

Der KI-Assistent sendet **nie** deinen Namen, deine E-Mail-Adresse oder Freitext aus deinem Pflanztagebuch an das Sprachmodell. An Kontext werden ausschließlich Stammwerte übermittelt: wissenschaftlicher Pflanzenname, aktuelle Phase, Substrat sowie numerische Messwerte (EC, pH). Diary-Einträge fließen — falls überhaupt — nur als anonymisierte Kennzahl ein (z. B. „zuletzt vor 5 Tagen gegossen"), nie als Originaltext. Jeder KI-Aufruf wird intern protokolliert, allerdings nur als Hash-Wert der Frage und deren Länge — nie im Klartext.

---

## Geplante Funktionen im Überblick

Die folgenden Funktionen sind als Baustein bereits implementiert, aber noch nicht in eine Pflanzen-, Pflanzdurchlauf- oder Aufgabenseite eingebunden — sie sind also noch nirgends sichtbar. Diese Abschnitte beschreiben das geplante Verhalten im Futur.

### Tipp-Karten

Tipp-Karten werden als kompakte Pflegehinweise auf der Detailseite einer Pflanze oder eines Pflanzdurchlaufs erscheinen. Das System wird den aktuellen Zustand analysieren und 2 bis 4 priorisierte Empfehlungen anzeigen (Titel, Erklärung, Empfehlung, Priorität) — bei der Erfahrungsstufe Anfänger maximal 2, kompakter und mit zugeklappten Quellen. Karten werden sich als erledigt oder nicht relevant markieren lassen.

### Tipp des Tages

Beim ersten Öffnen des Dashboards an einem Tag wird ein einzelner, für dich relevanter Tipp erscheinen — etwa ein Warnhinweis zu einem auffälligen Messwert, ein Hinweis auf einen anstehenden Phasenwechsel oder ein allgemeiner Pflegetipp. Der Tipp lässt sich für den Rest des Tages wegklicken.

### „Warum?"-Buttons

Auf Aufgabenkarten, Pflegeerinnerungen, Phasenwechsel-Vorschlägen und Düngeempfehlungen wird ein kleiner „Warum?"-Button erscheinen. Ein Klick öffnet ein Seitenpanel mit einer kurzen, KI-generierten Begründung auf Basis deiner aktuellen Pflanzendaten.

## Erfahrungsstufen und KI-Funktionen (geplant)

Die verfügbaren KI-Funktionen sollen sich künftig an die eingestellte [Erfahrungsstufe](../user-guide/onboarding.md) anpassen.

| Funktion | Beginner | Intermediate | Expert |
|----------|:--------:|:------------:|:------:|
| Wissensfragen | Ja | Ja | Ja |
| Tipp-Karten (vereinfacht, max. 2) | Ja | Ja | Ja |
| Tipp des Tages | Ja | Ja | Ja |
| „Warum?"-Buttons | Ja | Ja | Ja |
| Chat-Funktion | — | Ja | Ja |
| Quellen standardmäßig aufgeklappt | — | — | Ja |

Schon heute passt sich die Quellen-Darstellung (auf-/zugeklappt) an deine Erfahrungsstufe an; die übrigen Einschränkungen dieser Tabelle sind noch nicht umgesetzt — insbesondere ist der Chat aktuell für alle Erfahrungsstufen sichtbar.

---

## Für technische Nutzer / Self-Hoster {#fuer-technische-nutzer-self-hoster}

Der KI-Assistent wird über drei Ebenen freigeschaltet — Details und Umgebungsvariablen stehen unter [Umgebungsvariablen — KI-Assistent](../reference/environment-variables.md#ki-assistent).

**Stufe 1 (Betreiber):** `AI_FEATURES_ENABLED=true` am Backend. Ist die Variable nicht gesetzt, antworten sämtliche KI-Endpunkte mit HTTP 404 — die KI-API existiert für die Instanz dann faktisch nicht.

**Stufe 2 (Mandant):** Das Feld `tenant.settings.ai_features_enabled` steuert, ob KI-Funktionen für einen konkreten Garten (Mandanten) aktiv sind (Standard: `false`). Es gibt hierfür aktuell **weder eine Oberfläche noch einen eigenen API-Endpunkt** — das Feld lässt sich nur durch direkten Zugriff auf das Mandanten-Dokument in ArangoDB setzen. Ohne diesen Schritt bleiben alle mandantengebundenen KI-Funktionen (Chat, künftig Tipp-Karten) deaktiviert, selbst wenn Stufe 1 aktiv ist.

**Stufe 3 (Einwilligung):** `POST /api/v1/privacy/consents` mit `purpose: ai_tenant_data_access` bzw. `purpose: ai_cloud_processing` (siehe [Datenschutz & DSGVO](privacy.md#fuer-technische-nutzer-self-hoster)).

Die reine Wissensfrage benötigt ausschließlich Stufe 1 und ist als lastbegrenzter, anonymer Endpunkt erreichbar:

| Endpunkt | Zweck |
|----------|-------|
| `POST /api/v1/public/ai/ask` | Freie Wissensfrage ohne Pflanzenkontext (kein Login, IP-ratenbegrenzt) |
| `GET /api/v1/public/ai/health` | Prüft, ob die Wissensbasis erreichbar ist |

Details zu allen KI-Endpunkten (inkl. Chat, Tipps, Erklärungen) stehen in der [API-Referenz](../reference/api-reference.md#ki-assistent).

---

## Verhalten ohne erreichbare Wissensbasis

Ist die zugrunde liegende Wissensbasis (Knowledge Service) nicht erreichbar, liefert der KI-Assistent statt eines Fehlers eine regelbasierte Antwort ohne Sprachmodell — die Anwendung bleibt nutzbar, die Qualität der Antwort ist dann aber geringer.

---

## Häufige Fragen

??? question "Werden meine Pflanzdaten für das Training von KI-Modellen verwendet?"
    Nein. Kamerplanter sendet Daten ausschließlich zur Beantwortung deiner konkreten Anfrage. Eine Nutzung für Modell-Training hängt von den vertraglichen Bedingungen des vom Betreiber gewählten Providers ab — bei lokal betriebenen Modellen (Ollama) verlassen deine Daten dein Netzwerk grundsätzlich nie.

??? question "Warum antwortet der Chat mit „Die KI-Funktionen sind für diesen Garten aktuell deaktiviert"?"
    Stufe 1 (Betreiber) ist zwar aktiv, aber Stufe 2 (dein Garten/Mandant) noch nicht. Das lässt sich derzeit nur über einen direkten Eingriff des Betreibers beheben — siehe [Für technische Nutzer / Self-Hoster](#fuer-technische-nutzer-self-hoster).

??? question "Warum sehe ich beim Chat den Hinweis auf eine fehlende Einwilligung?"
    Der Chat nutzt deinen Pflanzenkontext und benötigt deshalb deine Einwilligung „KI-Zugriff auf deine Pflanzendaten". Wie du sie erteilst, steht unter [Einwilligung erteilen](#einwilligung-erteilen).

??? question "Kann ich den KI-Assistenten vollständig lokal betreiben?"
    Das entscheidet der Plattformbetreiber bei der Konfiguration der Wissensbasis. Mit einem lokalen Modell (Ollama) verlassen keine Daten das eigene Netzwerk und es ist keine Einwilligung zur Cloud-Verarbeitung nötig. Details für Selbsthoster: [KI-Provider einrichten](ai-providers.md).

---

## Siehe auch

- [KI-Provider einrichten](ai-providers.md)
- [Datenschutz & DSGVO](privacy.md)
- [RAG-Wissensbasis verstehen](../guides/rag-knowledge-base.md)
- [KI-Architektur (Entwickler)](../architecture/ai-architecture.md)
- [API-Referenz: KI-Assistent](../reference/api-reference.md#ki-assistent)
- [Umgebungsvariablen: KI-Assistent](../reference/environment-variables.md#ki-assistent)
