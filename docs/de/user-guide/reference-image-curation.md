# Referenzbilder kuratieren

Die Bilderkennung vergleicht das hochgeladene Foto eines Nutzers mit einem gespeicherten **Referenz-Index**: Für jede Pflanzenart sind mehrere lizenzfreie Referenzbilder hinterlegt, deren Merkmalsvektoren (DINOv2-Embeddings) als Vergleichswert dienen. Je sorgfältiger dieser Index kuratiert ist, desto treffsicherer arbeitet die Erkennung.

Als **Platform-Admin** kannst du einzelne Referenzbilder nach einem Sichttest manuell **abwählen**, damit sie das Erkennungsergebnis nicht mehr beeinflussen. Abgewählte Bilder bleiben im System erhalten (Audit-Trail) und können jederzeit wieder aufgenommen werden.

!!! note "Nur Platform-Admins"
    Die Kuratierung ist ausschließlich Nutzern mit der Plattform-Rolle **admin** zugänglich. Normale Nutzer sehen in der öffentlichen Galerie nur aktive Referenzbilder.

---

## Warum beeinflussen schlechte Referenzbilder die Erkennung?

Das System vergleicht das Nutzer-Foto mit jedem einzelnen Referenzbild einer Art — nicht mit einem einzigen Musterfoto. Ist ein Referenzbild ungeeignet, kann es zu falschen Übereinstimmungen führen:

| Bildproblem | Mögliche Auswirkung |
|------------|---------------------|
| **Unscharfes Bild** | Merkmalsvektoren sind unspezifisch; die Erkennung bevorzugt zufällig ähnliche Arten |
| **Falsches Organ** (z. B. Rinde statt Blatt) | Das System matcht über das falsche Pflanzenmerkmal |
| **Falsche Art** im Bild | Alle Fotos dieser Art werden durch das falsche Exemplar „verschmutzt" |
| **Duplikat** (dasselbe Foto mehrfach) | Übertriebene Gewichtung einer einzigen Perspektive |
| **Irrelevanter Bildinhalt** (Boden, Topf, Hintergrund) | Kein Pflanzenmerkmal vorhanden; verrauscht den Index |

Durch gezieltes Abwählen solcher Bilder steigerst du die Erkennungsgenauigkeit für die betroffene Art, ohne Daten dauerhaft zu verlieren.

---

## Referenzbild-Galerie aufrufen

1. Melde dich als Platform-Admin an.
2. Öffne die **Stammdaten-Übersicht** über das Seitenmenü.
3. Klicke auf eine **Pflanzenart** (z. B. *Monstera deliciosa*), um die Artendetailseite zu öffnen.
4. Wechsle zum Tab **Referenzbilder**.

Die Galerie zeigt alle Referenzbilder dieser Art. Abgewählte Bilder erscheinen ausgegraut und tragen das Label **Abgewählt**.

!!! tip "Abgewählte ausblenden"
    Sobald mindestens ein Bild abgewählt ist, erscheint oben der Schalter **Abgewählte Bilder ausblenden**. Eingeschaltet zeigt die Galerie nur noch die aktiven Bilder, die aktuell in der Erkennung verwendet werden. Sind dadurch keine Bilder mehr sichtbar, erscheint ein entsprechender Hinweis.

!!! tip "Zur Bildquelle springen"
    Jede Bildkachel hat unten rechts ein **Öffnen-Symbol** (↗). Ein Klick öffnet die Originalquelle des Bildes (GBIF, Wikimedia o. Ä.) in einem neuen Tab — nützlich, um Lizenz, Urheber und höher aufgelöste Varianten zu prüfen.

---

## Ein Bild abwählen

### Schritt 1: Bild im Sichttest beurteilen

Sieh dir das Referenzbild genau an. Typische Ausschlussgründe:

- Bild ist unscharf oder zu dunkel
- Zu sehen ist nicht das erwartete Pflanzenteil (z. B. Topf statt Blatt)
- Die abgebildete Pflanze sieht aus wie eine andere Art
- Das Bild taucht in der Galerie mehrfach auf (Duplikat)
- Der Bildinhalt ist nicht botanisch relevant (z. B. Etikettenfoto, reines Habitat-Bild)

### Schritt 2: Abwählen-Dialog öffnen

Klicke auf der Bildkachel unten rechts auf das **Abwählen-Symbol** (durchgestrichenes Auge). Es öffnet sich der Abwählen-Dialog.

### Schritt 3: Grund auswählen

Wähle im Dialog den passenden Ausschlussgrund:

| Grund | Wann verwenden |
|-------|---------------|
| **Unscharf** (`blurry`) | Bild zu unscharf für ein aussagekräftiges Merkmal |
| **Falsches Pflanzenteil** (`wrong_organ`) | Zeigt nicht das erwartete Organ (Blatt, Blüte, Frucht, Rinde) |
| **Falsche Art** (`wrong_species`) | Eine andere Art ist abgebildet |
| **Duplikat** (`duplicate`) | Dieses Bild ist bereits in anderer Form in der Galerie vorhanden |
| **Irrelevant** (`irrelevant`) | Kein nutzbarer Pflanzeninhalt (Boden, Topf, reine Habitats-Aufnahme) |
| **Manuell** (`manual`) | Sonstiger Grund (kein passender vorheriger Eintrag) |

### Schritt 4: Abwahl bestätigen

Klicke auf **Bestätigen**. Folgender Hinweis erscheint:

!!! warning "Wirkung der Abwahl"
    Dieses Bild wird aus der Bilderkennung entfernt. Es bleibt im System gespeichert und kann jederzeit wieder aufgenommen werden.

Nach der Bestätigung wird das Bild sofort aus dem aktiven Erkennungsindex ausgeschlossen. Die Änderung wirkt ab der nächsten Suchanfrage — laufende Identifikationen werden nicht unterbrochen.

---

## Coverage-Warnung beachten

Sinkt die Zahl aktiver Referenzbilder einer Art durch Abwahl unter **5**, erscheint in der Galerie folgende Warnung:

!!! warning "Erkennbarkeit eingeschraenkt"
    Diese Art hat noch **[n] aktive Referenzbilder** (Mindestschwelle: 5). Die Erkennung kann für diese Art unzuverlässig werden oder keine Treffer mehr liefern.

Ab diesem Punkt werden Nutzer bei der Foto-Identifikation ehrlich informiert, dass diese Art möglicherweise nicht sicher erkannt werden kann. Um die Erkennbarkeit wiederherzustellen, kannst du:

- Abgewählte Bilder wieder aufnehmen (wenn noch ausreichend geeignete vorhanden sind)
- Den Referenz-Index für diese Art neu befüllen (siehe [Bilderkennung in Betrieb nehmen](../deployment/inference-service.md))

---

## Ein abgewähltes Bild wieder aufnehmen

1. Öffne die Referenzbild-Galerie der betroffenen Art (Tab **Referenzbilder**).
2. Abgewählte Bilder sind standardmäßig sichtbar (graue Kachel mit Label **Abgewählt**). Falls der Schalter **Abgewählte Bilder ausblenden** aktiv ist, schalte ihn aus.
3. Klicke auf der grauen Kachel unten rechts auf das **Wieder-aufnehmen-Symbol** (Wiederherstellen).

Das Bild ist sofort wieder aktiv und wird bei der nächsten Erkennungsanfrage berücksichtigt.

!!! note "Audit-Trail"
    Jede Abwahl und jede Wiederaufnahme wird mit Zeitstempel, Ausschlussgrund und dem ausführenden Nutzer protokolliert. Das Protokoll ist im Bereich **Admin > Aktivitätsprotokoll** einsehbar.

---

## API-Zugriff (für Automatisierung)

Wenn du Kuratierungs-Aktionen skriptbasiert durchführen möchtest (z. B. Batch-Abwahl nach einem automatisierten Qualitätsscan), stehen folgende Endpunkte zur Verfügung:

**Alle Referenzbilder einer Art abrufen (inkl. abgewählter):**

```
GET /admin/reference-images/{species_key}/images
```

Antwortfeld `is_active: false` kennzeichnet abgewählte Bilder. Das Feld `exclusion_reason` enthält den gespeicherten Grund, `marked_at` den Zeitstempel der letzten Kuratierungsaktion.

**Bild ab- oder wieder aufnehmen:**

```
PATCH /admin/reference-images/{species_key}/images/{id}
```

Request-Body:

```json
{
  "is_active": false,
  "reason": "wrong_organ"
}
```

Zum Wieder-Aufnehmen:

```json
{
  "is_active": true,
  "reason": null
}
```

!!! note "Authentifizierung"
    Beide Endpunkte erfordern ein gültiges JWT mit der Plattform-Rolle **admin**. Für automatisierte Zugriffe empfiehlt sich ein [Service Account](../api/service-accounts.md).

---

## Häufige Fragen

??? question "Wird das Bild dauerhaft gelöscht, wenn ich es abwähle?"
    Nein. Die Abwahl ist ein Soft-Delete: Das Bild bleibt mit allen Metadaten (Quelle, Lizenz, Urheber, Embedding-Vektor) im System. Nur das Flag `is_active` wird auf `false` gesetzt. Du kannst das Bild jederzeit wieder aufnehmen.

??? question "Was passiert mit laufenden Erkennungsanfragen?"
    Bereits gestartete Erkennungsanfragen werden nicht unterbrochen. Das abgewählte Bild fließt in alle Anfragen ein, die nach der Abwahl gestartet werden. Die Änderung wirkt sofort für neue Anfragen.

??? question "Können normale Nutzer abgewählte Bilder sehen?"
    Nein. Die öffentliche Galerie (Artendetailseite für alle Nutzer) zeigt ausschließlich aktive Referenzbilder. Abgewählte Bilder sind nur in der Admin-Kuratierungsansicht sichtbar.

??? question "Wie viele Referenzbilder braucht eine Art für zuverlässige Erkennung?"
    Die Mindestschwelle liegt bei 5 aktiven Referenzbildern. Empfohlen sind 10–30 Bilder pro Art aus verschiedenen Winkeln und Wachstumsstadien. Unter 5 Bildern gibt das System bei der Erkennung eine Unsicherheitswarnung aus.

??? question "Wie wurden die Referenzbilder beschafft?"
    Die Referenzbilder werden automatisiert von GBIF und Wikimedia Commons bezogen — ausschließlich Bilder unter CC0- oder CC-BY-Lizenz. Die Beschaffungs-Pipeline filtert nach Qualitätskriterien (Mindestauflösung, Bildverhältnis), erkennt aber nicht alle inhaltlichen Mängel. Die manuelle Kuratierung ergänzt diese automatische Vorauswahl.

??? question "Kann ich einen eigenen Qualitätsscan automatisieren und die API verwenden?"
    Ja. Der `PATCH`-Endpunkt ist für genau diesen Anwendungsfall ausgelegt. Erstelle einen Service Account mit Admin-Rolle, führe deinen Qualitätsscan durch und rufe den Endpunkt für jedes abzuwählende Bild auf.

---

## Siehe auch

- [Pflanze per Foto identifizieren](plant-identification.md) — Endnutzer-Anleitung
- [Bilderkennung in Betrieb nehmen](../deployment/inference-service.md) — Referenz-Index befüllen und aktualisieren
- [Plattform-Admin-Bereich](admin.md) — Übersicht aller Admin-Funktionen
- [Service Accounts](../api/service-accounts.md) — Automatisierter API-Zugriff
