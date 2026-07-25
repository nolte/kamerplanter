# Mandanten & Gärten

Kamerplanter ist eine Multi-Tenant-Plattform: Deine Daten sind in **Tenants** (Mandanten) organisiert — isolierten Behältern, die genau einer Organisationsform entsprechen. Du kannst gleichzeitig Mitglied in mehreren Tenants sein, zum Beispiel in deinem privaten Balkongarten und im Gemeinschaftsgarten des Vereins.

---

## Was ist ein Tenant?

Ein Tenant ist der zentrale Isolations-Container für alle Ressourcen: Pflanzen, Standorte, Aufgaben, Ernten und Pflegedaten gehören immer zu genau einem Tenant. Andere Tenants können diese Daten nicht sehen.

| Tenant-Typ | Anwendungsfall | Beispiel |
|------------|---------------|---------|
| **Persönlich** | Privater Garten, Balkongarten, Zimmerpflanzen | Dein eigener Garten |
| **Organisation** | Gemeinschaftsgarten, Verein, Betrieb | "Grüne Oase e.V.", Cannabis-Anbauvereinigung |

### Persönlicher Tenant

Bei der Registrierung erstellt das System automatisch deinen **persönlichen Tenant**. Du bist dort automatisch Admin. Alle Ressourcen, die du in Kamerplanter anlegst, landen standardmäßig in deinem persönlichen Tenant.

!!! info "Persönliche Daten bleiben privat"
    Dein persönlicher Tenant ist vollständig von allen anderen Tenants isoliert. Kein Mitglied eines anderen Tenants kann deine privaten Zimmerpflanzen oder deinen Balkongarten sehen — auch wenn du demselben Gemeinschaftsgarten angehörst.

---

## Zwischen Tenants wechseln

Wenn du Mitglied in mehreren Tenants bist, siehst du in der Navigationsleiste einen **Tenant-Selektor** oben links.

1. Klicke auf den Tenant-Namen in der Navigationsleiste
2. Es öffnet sich ein Dropdown mit all deinen Tenants
3. Klicke auf den gewünschten Tenant — die Ansicht wechselt sofort

Der aktuell aktive Tenant ist in der Navigationsleiste hervorgehoben. Die URL enthält den Tenant-Slug: `/t/gruene-oase/standorte/...`

---

## Gemeinschaftsgarten erstellen

### Neuen Tenant anlegen

1. Klicke auf den Tenant-Selektor in der Navigationsleiste
2. Wähle **Neuen Garten erstellen**
3. Fülle das Formular aus:

    | Feld | Beschreibung | Beispiel |
    |------|-------------|---------|
    | **Name** | Anzeigename des Gartens | Grüne Oase e.V. |
    | **Slug** | URL-freundlicher Kurzname (auto-generiert) | gruene-oase |
    | **Typ** | Art der Organisation | Organisation |
    | **Beschreibung** | Kurze Beschreibung (optional) | Gemeinschaftsgarten im Westpark |

4. Klicke auf **Erstellen**

Du bist automatisch Admin des neuen Tenants.

---

## Mitglieder einladen

Als Admin kannst du Mitglieder auf drei Wegen einladen:

### Methode 1: E-Mail-Einladung

1. Navigiere zu **Einstellungen** > **Mitglieder** > **Einladen**
2. Gib die E-Mail-Adresse des Mitglieds ein
3. Wähle die Rolle (Admin, Gärtner, Beobachter)
4. Klicke auf **Einladung senden**

Das System sendet eine Einladungs-E-Mail. Nach Klick auf den Link im Mail wird der Nutzer deinem Tenant mit der vorgewählten Rolle hinzugefügt — egal ob er sich neu registriert oder bereits ein Konto hat.

### Methode 2: Einladungslink

1. Navigiere zu **Einstellungen** > **Mitglieder** > **Einladungslink generieren**
2. Stelle optional ein:
    - Maximale Anzahl Nutzungen (z.B. 20)
    - Ablaufdatum (z.B. in 30 Tagen)
    - Rolle, die neue Mitglieder erhalten
3. Kopiere den Link und teile ihn (WhatsApp, Aushang, E-Mail-Verteiler)

!!! tip "Ideal für große Gruppen"
    Der Einladungslink ist besonders praktisch für Gemeinschaftsgärten: Hänge ihn am Gartentor aus oder verschicke ihn im Vereins-Newsletter. Jeder mit dem Link kann beitreten, bis das Limit erreicht ist.

### Methode 3: OIDC (OpenID Connect) Auto-Join

Für Vereine und Organisationen mit eigenem Identity Provider (Keycloak, etc.) kann die OIDC-Integration so konfiguriert werden, dass neue Nutzer automatisch dem Tenant beitreten. Dies richtet der Plattform-Administrator ein.

---

## Rollen und Berechtigungen

Jedes Mitglied hat pro Tenant genau eine Rolle. Die Rolle bestimmt, was es tun darf:

### Rollenvergleich

| Aufgabe | Admin | Gärtner | Beobachter |
|---------|:-----:|:--------:|:----------:|
| Alles lesen | Ja | Ja | Ja |
| Pflanzen anlegen/bearbeiten | Ja | Ja | Nein |
| Standorte anlegen/bearbeiten | Ja | Ja | Nein |
| Aufgaben erstellen | Ja | Ja | Nein |
| Ernten dokumentieren | Ja | Ja | Nein |
| Mitglieder einladen | Ja | Nein | Nein |
| Rollen ändern | Ja | Nein | Nein |
| Tenant-Einstellungen ändern | Ja | Nein | Nein |

Die vollständige Rechteübersicht — inklusive Plattform-Rollen, Dienstkonten und der Frage, wer welche Daten zu sehen bekommt — steht unter [Rollen, Mandanten & Sichtbarkeit](../reference/roles-and-permissions.md).

!!! note "Geplante Gemeinschaftsfunktionen fehlen in dieser Tabelle"
    Pinnwand, Gießrotation und gemeinsame Einkaufsliste sind noch nicht implementiert (siehe [Gemeinschaftsfunktionen](#gemeinschaftsfunktionen) unten) und tauchen deshalb hier nicht als Berechtigung auf.

### Rollen ändern

1. Navigiere zu **Einstellungen** > **Mitglieder**
2. Klicke beim gewünschten Mitglied auf das Bearbeitungs-Symbol
3. Wähle die neue Rolle
4. Bestätigen — die Änderung gilt sofort

---

## Parzellen zuordnen

Ein Garten ist eine gemeinsame Arbeitsmenge: Alle Gärtner pflegen alle Pflanzen und Aufgaben. Eine Parzellen-Zuordnung hält deshalb fest, **wer sich kümmert** — sie sperrt niemanden aus.

- **Zugeordnete Parzellen**: Das Mitglied findet „seine" Parzelle schneller wieder; bearbeiten dürfen sie alle Gärtner.
- **Gemeinschaftsflächen** wie Kompost oder Gewächshaus brauchen gar keine Zuordnung.
- **Beobachter** lesen alles und ändern nichts — unabhängig von Zuordnungen.

Der praktische Vorteil: Fällt jemand kurzfristig aus, springt ein anderes Mitglied ein, ohne dass ein Admin erst etwas umstellen muss.

!!! tip "Etwas wirklich privat halten"
    Trennung verläuft immer an der Gartengrenze, nie innerhalb eines Gartens. Was nur dich etwas angeht, gehört in deinen persönlichen Garten — oder in einen weiteren Garten, den du jederzeit anlegen kannst.

!!! note "Teilweise verfügbar: Parzellen-Zuordnung"
    Zuordnungen lassen sich bislang nur über die Programmierschnittstelle anlegen — eine Bedienoberfläche dafür gibt es noch nicht. Einzelheiten unter [Rollen, Mandanten & Sichtbarkeit](../reference/roles-and-permissions.md#standort-zuweisungen-innerhalb-eines-gemeinschaftsgartens). <!-- REQ-049 §3.5 -->

---

## Gemeinschaftsfunktionen

!!! warning "Noch nicht implementiert"
    Pinnwand, Gießrotation und gemeinsame Einkaufsliste sind für Gemeinschaftsgärten geplant, aber aktuell weder im Backend noch in der Oberfläche vorhanden. Die folgenden Abschnitte beschreiben den vorgesehenen Funktionsumfang.

### Pinnwand

Die Pinnwand wird ein gemeinsamer Nachrichtenbereich für alle Tenant-Mitglieder sein: Mitglieder werden Beiträge veröffentlichen können, Admins werden Beiträge anpinnen und löschen können.

!!! example "Typische Pinnwand-Posts (Konzept)"
    - "Schneckenalarm! Bitte Bierfallen aufstellen."
    - "Samstag 10 Uhr: Gemeinsames Kompost-Umsetzen."
    - "Zu viele Zucchini — wer will welche?"

### Gießrotation

Für die Verteilung von Gießpflichten unter Mitgliedern ist eine Rotationsfunktion geplant: Ein Intervall (z. B. wöchentlich) und die beteiligten Mitglieder werden hinterlegbar sein, und das System wird das jeweils zuständige Mitglied erinnern. Mitglieder sollen Dienste untereinander tauschen können, ohne den Admin einzubeziehen.

### Gemeinsame Einkaufsliste

Eine gemeinsame Einkaufsliste ist geplant: Alle Gärtner sollen Einträge hinzufügen und abhaken können, Admins sollen Listen archivieren können.

---

## Tenant-Einstellungen

Als Admin erreichst du alle Einstellungen unter **Einstellungen** (Zahnrad-Icon).

### Wichtige Einstellungen

| Einstellung | Beschreibung |
|-------------|-------------|
| **Name & Slug** | Anzeigename und URL-Kurzname |
| **Stammdaten-Zuweisung** | Welche globalen Pflanzenarten sind sichtbar |
| **Einladungseinstellungen** | Standard-Rolle für neue Mitglieder |
| **OIDC-Konfiguration** | Auto-Join über externen Identity Provider |

!!! warning "Slug ändern bricht URLs"
    Wenn du den Slug änderst, ändern sich alle URLs innerhalb des Tenants. Lesezeichen und geteilte Links werden ungültig. Ändere den Slug nur, wenn nötig.

---

## Tenant verlassen

Du kannst einen Tenant verlassen, solange du nicht der einzige Admin bist:

1. Navigiere zu **Einstellungen** > **Mitgliedschaft** > **Tenant verlassen**
2. Bestätigen

!!! warning "Als einziger Admin"
    Wenn du der einzige Admin bist, musst du vorher entweder ein anderes Mitglied zum Admin befördern oder den Tenant löschen.

---

## Häufige Fragen

??? question "Kann ich Daten zwischen Tenants teilen?"
    Nein — Ressourcen gehören immer zu genau einem Tenant. Cross-Tenant-Sharing ist bewusst nicht möglich, um Datenisolation zu gewährleisten. Globale Stammdaten (Pflanzenarten, Schädlinge) sind hingegen für alle Tenants sichtbar.

??? question "Wie viele Tenants kann ich erstellen?"
    Es gibt keine technische Begrenzung. Du kannst beliebig viele Tenants erstellen und beitreten.

??? question "Was passiert mit meinen Daten, wenn ich einen Tenant lösche?"
    Alle Ressourcen des Tenants werden gelöscht. Dein persönlicher Tenant und deine Mitgliedschaften in anderen Tenants sind davon nicht betroffen.

??? question "Sehen Tenant-Admins meine persönlichen Zimmerpflanzen?"
    Nein. Dein persönlicher Tenant ist vollständig von allen anderen Tenants isoliert. Selbst wenn ein Admin im Gemeinschaftsgarten mehr Rechte hat, kann er niemals Daten in deinem persönlichen Tenant sehen.

---

## Siehe auch

- [Rollen, Mandanten & Sichtbarkeit](../reference/roles-and-permissions.md)
- [Erste Schritte — Onboarding](onboarding.md)
- [Konto & Anmeldung](account.md)
- [Standorte & Substrate](locations-substrates.md)
