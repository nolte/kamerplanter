# Vermehrungsmanagement

!!! warning "Noch nicht implementiert"
    Diese Funktion ist **spezifiziert aber noch nicht implementiert**. Die Dokumentation beschreibt das geplante Verhalten. Aktuell existieren Familien-Beziehungen und Artenstammdaten mit Vermehrungsmethoden, aber der Abstammungsgraph (`descended_from`-Edges), Klon-Tracking und Veredelungs-Kompatibilitätsprüfung fehlen noch. <!-- REQ-017 -->

Kamerplanter dokumentiert die genetische Abstammung deiner Pflanzen lückenlos: Welche Mutterpflanze lieferte den Steckling? Welche zwei Elternpflanzen wurden gekreuzt? Über welche Unterlage wurde eine Sorte veredelt? Der **Abstammungsgraph** macht diese Beziehungen sichtbar und prüft automatisch Veredelungskompatibilität.

---

## Voraussetzungen

- Mindestens eine Pflanzinstanz (Mutterpflanze) ist angelegt
- Die Art und Sorte sind in den Stammdaten erfasst

---

## Vermehrungsmethoden im Überblick

| Methode | Beschreibung | Genetische Beziehung |
|---------|-------------|---------------------|
| **Steckling (Klon)** | Bewurzelter Trieb der Mutterpflanze | Genetisch identisch |
| **Samen-Kreuzung** | Samen aus kontrollierter Bestäubung | 50% Genetik je Elternteil |
| **Veredelung** | Edelreis auf Unterlage aufgebracht | Edelreis bleibt genetisch unverändert |
| **Teilung** | Pflanze in mehrere Teile geteilt | Genetisch identisch (wie Klon) |

!!! note "Vermehrungsarten im Arten-Steckbrief"
    Im **Arten-Steckbrief** (Stammdaten > Arten) gibt es das Feld **Vermehrungsarten** (`propagation_methods`). Dort ist hinterlegt, welche Methoden für eine Art **generell üblich** sind — z.B. Tomate: Aussaat + Steckling. Das Feld ist eine Mehrfachauswahl aus 13 Methoden und wird ab der Erfahrungsstufe **Fortgeschrittener** angezeigt. Alle vorgefertigten Kulturpflanzen-Stammdaten enthalten bereits diese Information. Weitere Details: [Stammdaten verwalten — Vermehrungsarten](plant-management.md#vermehrungsarten-propagation_methods).

---

## Stecklinge (Klone) nehmen

Stecklinge sind die häufigste Vermehrungsmethode bei Zimmerpflanzen und im Growzelt. Das System verfolgt jede Klongeneration.

### Neuen Steckling anlegen

1. Navigiere zu **Pflanzen** > Mutterpflanze
2. Klicke auf **Vermehren** > **Steckling nehmen**
3. Fülle das Formular aus:

    | Feld | Beschreibung | Beispiel |
    |------|-------------|---------|
    | **Anzahl Stecklinge** | Wie viele Stecklinge werden genommen | 4 |
    | **Datum** | Datum der Entnahme | 2026-03-28 |
    | **Standort** | Wo werden die Stecklinge bewurzelt | Anzuchtzelt |
    | **Substrat** | Bewurzelungssubstrat | Steinwolle-Plugs |
    | **Notizen** | Methode, Hormonpulver, etc. | Auxin-Pulver, 45°-Schnitt |

4. Klicke auf **Stecklinge anlegen**

Das System erstellt automatisch neue Pflanzinstanzen mit dem `descended_from`-Edge zur Mutterpflanze.

!!! tip "Klon-Generationen tracken"
    Wenn ein Steckling selbst wieder als Mutterpflanze genutzt wird, entsteht eine Klon-Kette: Mutter → F1-Klon → F2-Klon. Diese Kette ist in der Abstammungsansicht als Graph sichtbar.

### Bewurzelungsstatus verfolgen

1. Navigiere zu **Pflanzen** > gewünschter Steckling
2. Tab **Wachstumsphasen** zeigt die aktuelle Phase (Keimung/Vermehrung)
3. Wenn die Wurzeln sichtbar sind: Phasenwechsel zu **Sämling** ausführen

---

## Samen-Kreuzungen dokumentieren

Für kontrollierte Bestäubungen — z.B. zur Zucht neuer Sorten:

### Kreuzung anlegen

1. Navigiere zu **Stammdaten** > **Sorten** > **Neue Sorte**
2. Unter dem Abschnitt **Genetische Herkunft**:
    - **Mutterpflanze** (Samenpflanze) auswählen
    - **Vaterpflanze** (Pollenpflanze) auswählen
    - **Kreuzungsdatum** eintragen
3. Speichern

Das System legt `descended_from`-Edges zu beiden Elternpflanzen an und markiert die neue Sorte als F1-Hybride.

!!! example "Beispiel: Tomatenzüchtung"
    Du kreuzst "San Marzano" (Mutter) mit "Sungold" (Vater). Das System erstellt eine neue Sorte "San Marzano × Sungold (F1)" mit beiden Abstammungs-Kanten im Graph.

---

## Veredelung

Veredelung wird eingesetzt, um eine wertvolle Sorte (Edelreis) auf eine robuste Unterlage aufzubringen.

### Veredelung anlegen

1. Navigiere zu **Pflanzen** > Edelreis-Pflanze > **Vermehren** > **Veredelung**
2. Wähle die **Unterlage** (muss kompatibel sein)
3. Dokumentiere Methode (Kopulation, Okulation, etc.) und Datum

### Kompatibilitätsprüfung

Das System prüft automatisch die Gattungs- und Familienkompatibilität:

<!-- diagram-source: user-described — graft compatibility check decision tree (genus, then family) -->
```mermaid
flowchart TD
    A[Create graft] --> B{Same genus?}
    B -->|Yes| OK[Compatible]
    B -->|No| C{Same family?}
    C -->|Yes| W[Warning: Compatibility possible, check]
    C -->|No| E[Error: Incompatible]
```

!!! warning "Kompatibilitätsregeln"
    Kompatibilität wird auf Gattungs- und Familienebene geprüft. Tomaten auf Kartoffel-Unterlage (beide Solanum) sind kompatibel. Tomate auf Apfel-Unterlage (Solanaceae / Rosaceae) sind inkompatibel.

---

## Pflanzenteilung

Für Stauden, Zwiebelgewächse und buschige Zimmerpflanzen:

1. Navigiere zu **Pflanzen** > gewünschte Pflanze > **Vermehren** > **Teilen**
2. Lege fest, in wie viele Teile geteilt wird
3. Das System erstellt neue Pflanzinstanzen mit `descended_from`-Edge

---

## Der Abstammungsgraph

Die Abstammungsansicht zeigt alle Eltern-, Geschwister- und Nachkommenpflanzen in einer interaktiven Grafik.

### Graph öffnen

1. Navigiere zu **Pflanzen** > gewünschte Pflanze
2. Klicke auf den Tab **Abstammung**

<!-- diagram-source: user-described — plant lineage graph: mother plant with F1 clones and an F2 clone via descended_from edges -->
```mermaid
flowchart TB
    M["Mother plant<br/>(origin)"]
    K1["Clone F1-1"]
    K2["Clone F1-2"]
    K3["Clone F1-3"]
    K2_1["Clone F2-1<br/>(from F1-2)"]
    M -->|descended_from| K1
    M -->|descended_from| K2
    M -->|descended_from| K3
    K2 -->|descended_from| K2_1
```

Im Graph sind sichtbar:
- **Mutterpflanze** (Quelle des Stecklings)
- **Geschwister-Klone** (andere Stecklinge derselben Mutter)
- **Nachkommen** (Stecklinge dieses Klons)
- **Kreuzungspartner** bei Samen-Kreuzungen
- **Unterlage** bei Veredelungen

!!! tip "Klon-Linien im Growzelt"
    Im professionellen Anbau ist die Klon-Linie entscheidend: Ein Klon von Generation F3 kann schwächere Eigenschaften zeigen als F1. Der Graph macht solche Linien transparent.

---

## Häufige Fragen

??? question "Ich habe einen Steckling genommen, aber vergessen das in der App einzutragen — kann ich das nachträglich anlegen?"
    Ja. Du kannst beim Anlegen einer neuen Pflanzinstanz immer eine Mutterpflanze und ein historisches Entnahmedatum eintragen. Der Abstammungsgraph wird dann korrekt aufgebaut.

??? question "Kann eine Pflanze mehrere Mutterpflanzen haben?"
    Bei Samen-Kreuzungen ja — eine Pflanze hat genau zwei Elternpflanzen (Mutter + Vater). Bei Stecklingen und Teilungen hat sie genau eine. Veredelungen haben Edelreis + Unterlage, wobei die Genetik vom Edelreis stammt.

??? question "Wie erkenne ich, ob eine Sorte aus einem Steckling oder aus Samen stammt?"
    Im Profil der Pflanzinstanz unter dem Tab **Abstammung** siehst du die Vermehrungsmethode des `descended_from`-Edges (Steckling, Samen, Veredelung, Teilung).

??? question "Die Kompatibilitätsprüfung schlägt fehl, obwohl ich weiß, dass es funktioniert."
    Das System prüft nach botanischer Familie/Gattung. Du kannst die Prüfung übersteuern und manuell einen Kompatibilitäts-Vermerk hinzufügen. Trage die beobachtete Kompatibilität als Notiz in die Pflanzinstanz ein.

---

## Siehe auch

- [Pflanzdurchläufe](planting-runs.md)
- [Stammdaten verwalten](plant-management.md)
- [Wachstumsphasen](growth-phases.md)
