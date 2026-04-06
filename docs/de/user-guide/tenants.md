# Mandanten & Gaerten

Kamerplanter ist eine Multi-Tenant-Plattform: Deine Daten sind in **Tenants** (Mandanten) organisiert — isolierten Behaeltern, die genau einer Organisationsform entsprechen. Du kannst gleichzeitig Mitglied in mehreren Tenants sein, zum Beispiel in deinem privaten Balkongarten und im Gemeinschaftsgarten des Vereins.

---

## Was ist ein Tenant?

Ein Tenant ist der zentrale Isolations-Container fuer alle Ressourcen: Pflanzen, Standorte, Aufgaben, Ernten und Pflegedaten gehoeren immer zu genau einem Tenant. Andere Tenants koennen diese Daten nicht sehen.

| Tenant-Typ | Anwendungsfall | Beispiel |
|------------|---------------|---------|
| **Persoenlich** | Privater Garten, Balkongarten, Zimmerpflanzen | Dein eigener Garten |
| **Organisation** | Gemeinschaftsgarten, Verein, Betrieb | "Gruene Oase e.V.", Cannabis-Anbauvereinigung |

### Persoenlicher Tenant

Bei der Registrierung erstellt das System automatisch deinen **persoenlichen Tenant**. Du bist dort automatisch Admin. Alle Ressourcen, die du in Kamerplanter anlegst, landen standardmaessig in deinem persoenlichen Tenant.

!!! info "Persoenliche Daten bleiben privat"
    Dein persoenlicher Tenant ist vollstaendig von allen anderen Tenants isoliert. Kein Mitglied eines anderen Tenants kann deine privaten Zimmerpflanzen oder deinen Balkongarten sehen — auch wenn du demselben Gemeinschaftsgarten angehoerst.

---

## Zwischen Tenants wechseln

Wenn du Mitglied in mehreren Tenants bist, siehst du in der Navigationsleiste einen **Tenant-Selektor** oben links.

1. Klicke auf den Tenant-Namen in der Navigationsleiste
2. Es oeffnet sich ein Dropdown mit all deinen Tenants
3. Klicke auf den gewuenschten Tenant — die Ansicht wechselt sofort

Der aktuell aktive Tenant ist in der Navigationsleiste hervorgehoben. Die URL enthalt den Tenant-Slug: `/t/gruene-oase/standorte/...`

---

## Gemeinschaftsgarten erstellen

### Neuen Tenant anlegen

1. Klicke auf den Tenant-Selektor in der Navigationsleiste
2. Waehle **Neuen Garten erstellen**
3. Fuelle das Formular aus:

    | Feld | Beschreibung | Beispiel |
    |------|-------------|---------|
    | **Name** | Anzeigename des Gartens | Gruene Oase e.V. |
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
3. Waehle die Rolle (Admin, Gaertner, Beobachter)
4. Klicke auf **Einladung senden**

Das System sendet eine Einladungs-E-Mail. Nach Klick auf den Link im Mail wird der Nutzer deinem Tenant mit der vorgewaehlten Rolle hinzugefuegt — egal ob er sich neu registriert oder bereits ein Konto hat.

### Methode 2: Einladungslink

1. Navigiere zu **Einstellungen** > **Mitglieder** > **Einladungslink generieren**
2. Stelle optional ein:
    - Maximale Anzahl Nutzungen (z.B. 20)
    - Ablaufdatum (z.B. in 30 Tagen)
    - Rolle, die neue Mitglieder erhalten
3. Kopiere den Link und teile ihn (WhatsApp, Aushang, E-Mail-Verteiler)

!!! tip "Ideal fuer grosse Gruppen"
    Der Einladungslink ist besonders praktisch fuer Gemeinschaftsgaerten: Haenge ihn am Gartentor aus oder verschicke ihn im Vereins-Newsletter. Jeder mit dem Link kann beitreten, bis das Limit erreicht ist.

### Methode 3: OIDC Auto-Join

Fuer Vereine und Organisationen mit eigenem Identity Provider (Keycloak, etc.) kann die OIDC-Integration so konfiguriert werden, dass neue Nutzer automatisch dem Tenant beitreten. Dies richtet der Plattform-Administrator ein.

---

## Rollen und Berechtigungen

Jedes Mitglied hat pro Tenant genau eine Rolle. Die Rolle bestimmt, was es tun darf:

### Rollenvergleich

| Aufgabe | Admin | Gaertner | Beobachter |
|---------|:-----:|:--------:|:----------:|
| Alles lesen | Ja | Ja | Ja |
| Pflanzen anlegen/bearbeiten | Ja | Ja | Nein |
| Standorte anlegen/bearbeiten | Ja | Nein* | Nein |
| Aufgaben erstellen | Ja | Ja | Nein |
| Ernten dokumentieren | Ja | Ja | Nein |
| Mitglieder einladen | Ja | Nein | Nein |
| Rollen aendern | Ja | Nein | Nein |
| Tenant-Einstellungen aendern | Ja | Nein | Nein |
| Pinwand-Posts pinnen | Ja | Nein | Nein |
| Einkaufsliste verwalten | Ja | Ja | Nein |
| Giessrotation erstellen | Ja | Nein | Nein |

*Gaertner koennen Standorte bearbeiten, die ihnen zugewiesen sind.

### Rollen aendern

1. Navigiere zu **Einstellungen** > **Mitglieder**
2. Klicke beim gewuenschten Mitglied auf das Bearbeitungs-Symbol
3. Waehle die neue Rolle
4. Bestaetigen — die Aenderung gilt sofort

---

## Standort-basierte Schreibrechte

In einem Gemeinschaftsgarten kann nicht jedes Mitglied jede Parzelle bearbeiten. Das **Zuweisungssystem** regelt, wer welche Standorte bearbeiten darf:

### Standort einem Mitglied zuweisen

1. Navigiere zu **Standorte** > gewuenschter Standort
2. Klicke auf **Zuweisung bearbeiten**
3. Waehle das Mitglied aus dem Dropdown
4. Klicke auf **Speichern**

**Regeln fuer Standort-Zuweisungen:**

- **Zugewiesene Standorte**: Nur der zugewiesene Gaertner und Admins duerfen bearbeiten
- **Nicht zugewiesene Standorte**: Alle Gaertner des Tenants duerfen bearbeiten (Gemeinschaftsflaechen)
- **Beobachter**: Lesen immer alles, unabhaengig von Zuweisungen
- **Admins**: Koennen immer alles bearbeiten

!!! example "Typischer Gemeinschaftsgarten"
    Der Gemeinschaftsgarten hat 20 Parzellen (je einer Person zugewiesen), einen Kompostbereich und ein Gewächshaus (beide nicht zugewiesen, also fuer alle Gaertner bearbeitbar).

---

## Gemeinschaftsfunktionen

### Pinwand

Die Pinwand ist ein gemeinsamer Nachrichtenbereich fuer alle Tenant-Mitglieder.

1. Navigiere zu **Gemeinschaft** > **Pinwand**
2. Klicke auf **Neuer Post**
3. Schreibe deine Nachricht und klicke auf **Veroeffentlichen**

Admins koennen Posts anpinnen, sodass sie oben erscheinen, und Posts loeschen.

!!! example "Typische Pinwand-Posts"
    - "Schneckenalarm! Bitte Bierfallen aufstellen."
    - "Samstag 10 Uhr: Gemeinsames Kompost-Umsetzen."
    - "Zu viele Zucchini — wer will welche?"

### Giessrotation

Fuer die Verteilung von Giesspflichten unter Mitgliedern:

1. Navigiere zu **Gemeinschaft** > **Giessrotation**
2. Klicke auf **Neue Rotation erstellen**
3. Lege das Intervall fest (z.B. woechentlich) und trage die Mitglieder ein
4. Das System erinnert jede Woche das zustaendige Mitglied

Mitglieder koennen Dienste untereinander tauschen — ohne den Admin einzubeziehen.

### Gemeinsame Einkaufsliste

1. Navigiere zu **Gemeinschaft** > **Einkaufsliste**
2. Alle Gaertner koennen Eintraege hinzufuegen und abhaken
3. Admins koennen Listen archivieren

---

## Tenant-Einstellungen

Als Admin erreichst du alle Einstellungen unter **Einstellungen** (Zahnrad-Icon).

### Wichtige Einstellungen

| Einstellung | Beschreibung |
|-------------|-------------|
| **Name & Slug** | Anzeigename und URL-Kurzname |
| **Stammdaten-Zuweisung** | Welche globalen Pflanzenarten sind sichtbar |
| **Einladungseinstellungen** | Standard-Rolle fuer neue Mitglieder |
| **OIDC-Konfiguration** | Auto-Join ueber externen Identity Provider |

!!! warning "Slug aendern bricht URLs"
    Wenn du den Slug aenderst, aendern sich alle URLs innerhalb des Tenants. Lesezeichen und geteilte Links werden ungueltig. Aendere den Slug nur, wenn noetig.

---

## Tenant verlassen

Du kannst einen Tenant verlassen, solange du nicht der einzige Admin bist:

1. Navigiere zu **Einstellungen** > **Mitgliedschaft** > **Tenant verlassen**
2. Bestaetigen

!!! warning "Als einziger Admin"
    Wenn du der einzige Admin bist, musst du vorher entweder ein anderes Mitglied zum Admin befoerdern oder den Tenant loeschen.

---

## Haeufige Fragen

??? question "Kann ich Daten zwischen Tenants teilen?"
    Nein — Ressourcen gehoeren immer zu genau einem Tenant. Cross-Tenant-Sharing ist bewusst nicht moeglich, um Datenisolation zu gewaehrleisten. Globale Stammdaten (Pflanzenarten, Schädlinge) sind hingegen fuer alle Tenants sichtbar.

??? question "Wie viele Tenants kann ich erstellen?"
    Es gibt keine technische Begrenzung. Du kannst beliebig viele Tenants erstellen und beitreten.

??? question "Was passiert mit meinen Daten, wenn ich einen Tenant losche?"
    Alle Ressourcen des Tenants werden geloescht. Dein persoenlicher Tenant und deine Mitgliedschaften in anderen Tenants sind davon nicht betroffen.

??? question "Sehen Tenant-Admins meine persoenlichen Zimmerpflanzen?"
    Nein. Dein persoenlicher Tenant ist vollstaendig von allen anderen Tenants isoliert. Selbst wenn ein Admin im Gemeinschaftsgarten mehr Rechte hat, kann er niemals Daten in deinem persoenlichen Tenant sehen.

---

## Siehe auch

- [Erste Schritte — Onboarding](onboarding.md)
- [Benutzerkonten & Authentifizierung](../api/authentication.md)
- [Standorte & Substrate](locations-substrates.md)
