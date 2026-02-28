# Zielgruppen- und Anwendungsgebietsanalyse
**Erstellt von:** Zielgruppen-Analyst
**Datum:** 2026-02-27
**Analysierte Dokumente:** 21 funktionale Anforderungen (REQ-001 bis REQ-021), 10 non-funktionale Anforderungen (NFR-001 bis NFR-010), 12 UI-NFR-Dokumente (UI-NFR-001 bis UI-NFR-012), GLOSSAR, stack.md
**Methodik:** Implizite/Explizite Signalextraktion, Jobs-to-be-Done-Mapping, Markt-Gap-Analyse, Persona-Gap-Analyse

---

## Executive Summary

Kamerplanter adressiert mit seinen 21 funktionalen Anforderungen primär den **erfahrenen Indoor-Grower und ambitionierten Hobby-Anbauer**, der kontrollierteBedingungen (Growzelt, Hydroponik, Sensorik, Automatisierung) einsetzt. Daneben gibt es ein klares sekundares Signal Richtung **Cannabis-Anbau** (Trichom-Analyse, THC-Gehalt, Karenzzeiten, Otreeba-Integration, SOG/SCROG-Templates) sowie einen wachsenden Fokus auf **Gemuse- und Krauteranbau**. Mit REQ-020 (Onboarding-Wizard) und REQ-021 (Erfahrungsstufen) hat das System explizit begonnen, Einsteiger zu adressieren.

Die groste Lucke liegt bei **professionellen Gewachshaus-Betrieben und Mikro-Farmen**, die Multi-User-Betrieb, Rollenkonzepte, Compliance-Dokumentation und wirtschaftliche Auswertungen benotigen. Ebenso unterversorgt sind **Zimmerpflanzen-Liebhaber** (Zimmerpflanzen-Templates in REQ-006 zeigen ein Signal, sind aber nicht systematisch ausgebaut) und **Aquaponik-Betreiber**. Das groszte ungenutzte Potenzial liegt in der Erschliesung von **Bildungs- und Forschungseinrichtungen** sowie der **professionellen Mikro-Farm** durch gezielte Erganzungen bei Rollen, Reporting und Compliance.

---

## 1. Aktuell adressierte Nutzergruppen

### Primäre Zielgruppen (stark adressiert)

#### ZG-001: Ambitionierter Indoor-Grower (Growzelt / Hydroponik)
| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Indoor-Grower (Hydroponik/Coco/Soil) |
| **Profil** | Person mit 1-3 Jahren Erfahrung, betreibt 1-4 Growzelte, kennt EC/VPD/NPK, kauft hochwertige Dunger, dokumentiert manuell oder mit Excel |
| **Betriebsgrose** | 5-50 Pflanzen, 1-6 m² Anbauflache |
| **Technische Affinitat** | Hoch |
| **Kernbedurfnis** | Optimierung von Ertrag und Qualitat durch prazise Nahrtstoffsteuerung, Phasenmanagement und Klimakontrolle |
| **Evidenz** | REQ-003 (Phasensteuerung mit VPD-Profilen), REQ-004 (Multi-Part-Dunger, CalMag-Mischreihenfolge, EC-Budget), REQ-005 (Hybrid-Sensorik), REQ-014 (Tankmanagement, DWC/Hydro-Typen), REQ-018 (VPD-Regelkreis, Lichtsteuerung), REQ-019 (Steinwolle, Coco, Blahton) |
| **Abdeckungsgrad** | Vollstandig |

**Beleg-Details:** REQ-004 nennt explizit "CalMag vor Sulfaten", "EC-net = Ziel-EC minus Basis-EC", Misch-Prioritaten fur A/B-Komponenten. REQ-014 differenziert Tanktypen DWC/NFT/Ebb&Flow. REQ-006 beinhaltet fertige Templates fur "Cannabis SOG", "Cannabis SCROG", "Cannabis Mainlining".

---

#### ZG-002: Cannabis-Anbauer (regulierter / nicht-regulierter Bereich)
| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Cannabis-Grower |
| **Profil** | Anbauer medizinischer oder regulierter Cannabis-Pflanzen; kennt Fachbegriffe wie Trichom, Phenotyp, Kreuzung, Karenzzeit |
| **Betriebsgrose** | 1-100+ Pflanzen (Eigenanbau bis kleine Lizenzanlage) |
| **Technische Affinitat** | Mittel bis Hoch |
| **Kernbedurfnis** | Genetische Ruckverfolgbarkeit (Seed-to-Shelf), Trichom-basierte Reifegradprufung, Karenzzeit-Dokumentation, Sorten-Management |
| **Evidenz** | REQ-001 (Cannabaceae als Seed-Daten-Familie), REQ-006 (SOG/SCROG/Mainlining-Templates), REQ-007 (Trichom-Mikroskopie-Indikatoren, Pistil-Farbung), REQ-011 (Otreeba als Cannabis-Sorten-API), REQ-017 (Mutterpflanzen, Klonlinie, Generationszahler), REQ-013 (Klon-Runs), REQ-008 (Jar-Curing-Protokoll) |
| **Abdeckungsgrad** | Vollstandig |

**Beleg-Details:** REQ-001 Szenario 4 beschreibt explizit "Cannabis (Cannabis sativa) als Kurztagspflanze". REQ-007 beschreibt Trichom-Phasen (klar/milchig/bernstein) mit THC-Angaben. REQ-011 bindet die Otreeba-API fur "Cannabis-Genetik, Effekte, Blutezeit, Strain-Typ" an.

---

#### ZG-003: Gemuse- und Krautergartner (Indoor/Outdoor, ambitioniert)
| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Nutzpflanzen-Gartner (ambitioniert) |
| **Profil** | Gartner mit Hochbeeten, Balkon-Gemuseanbau oder Kleingarten; interessiert an Mischkultur, Fruchtfolge, Sortenwahl und optimalem Erntezeitpunkt |
| **Betriebsgrose** | 10-200 Pflanzen, 10-100 m² Flache |
| **Technische Affinitat** | Mittel |
| **Kernbedurfnis** | Fruchtfolge-Optimierung, Sortenverwaltung, Erntezeitpunkt-Bestimmung, Schutzmastnahmen |
| **Evidenz** | REQ-001 (Fruchtfolge-Engine, Mischkultur-Matrix, 9 Pflanzenfamilien), REQ-002 (Outdoor/Hochbeet-Typen, GPS-Koordinaten), REQ-007 (Ernte-Indikatoren fur Tomate/Paprika/Gurken/Salat/Wurzelgemuse), REQ-010 (IPM), REQ-013 (Mischkultur-Run: Tomate+Basilikum+Tagetes) |
| **Abdeckungsgrad** | Stark |

**Beleg-Details:** REQ-001 enthalt als Seed-Szenario explizit "Szenario 1: Basilikum" und "Szenario 6: Brokkoli Fruchtfolge". REQ-013 Szenario 3 zeigt Mischkultur "Beet B Sommer 2025" mit Tomate+Basilikum+Tagetes.

---

### Sekundäre Zielgruppen (teilweise adressiert)

#### ZG-004: Systemadministrator / technischer Betreiber
| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | System-Admin / Betreiber |
| **Profil** | Technische Person, die das System einrichtet, Stammdaten pflegt und externe Integrationen verwaltet |
| **Betriebsgrose** | Betriebsubergreifend |
| **Technische Affinitat** | Sehr hoch |
| **Kernbedurfnis** | Datenpflege, API-Integration, Bulk-Import, Systemstabilitat |
| **Evidenz** | REQ-011 (User Story "Als Systemadministrator"), REQ-012 (CSV-Import, "Als Systemadministrator"), NFR-007 (Betriebsstabilitat), NFR-008 (Teststrategie) |
| **Abdeckungsgrad** | Vollstandig |

---

#### ZG-005: Hobby-Einsteiger / Beginner-Gartner
| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Hobby-Einsteiger |
| **Profil** | Gartner ohne Vorerfahrung; 3 Tomaten auf dem Balkon oder Krauter auf der Fensterbank; versteht keine Fachbegriffe wie VPD, EC, PPFD |
| **Betriebsgrose** | 1-20 Pflanzen |
| **Technische Affinitat** | Gering |
| **Kernbedurfnis** | Einfacher Einstieg ohne Fachhurden, verstandliche Pflege-Erinnerungen, Fehlervermeidung |
| **Evidenz** | REQ-020 (Onboarding-Wizard, User Story "Als Hobby-Gartner...in weniger als 3 Minuten", Starter-Kits "Krauter auf der Fensterbank", "Tomaten auf dem Balkon"), REQ-021 (Einsteiger-Modus, 43 identifizierte Hurden), UI-NFR-011 Fachbegriffe (16 unerklaerte Fachbegriffe identifiziert) |
| **Abdeckungsgrad** | Teilweise |

**Abdeckungsluken:** Starter-Kits sind definiert, aber die Auswahl ist auf den Wizard beschrankt. Es fehlt ein dauerhaft vereinfachter Workflow fur Routineaufgaben (Giesserinnerung, Dungekalender in Klarsprache) sowie gamifizierte Fortschrittsdarstellung.

---

#### ZG-006: Professioneller Gewachshaus-Betreiber / Mikro-Farm
| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Semi-professioneller Betreiber / Mikro-Farm |
| **Profil** | Betreiber einer kleinen kommerziellen Anlage (Urban Farm, Lizenzbetrieb, Gastronomie-Lieferant); benotigt Compliance-Dokumentation, Mitarbeiter-Koordination und wirtschaftliche Auswertungen |
| **Betriebsgrose** | 100-1000 Pflanzen, 50-500 m² |
| **Technische Affinitat** | Mittel bis Hoch |
| **Kernbedurfnis** | Rollen-basierter Mehrbenutzerbetrieb, Audit-Trails, Ertragskostenrechnung, Lagerbestandsverwaltung |
| **Evidenz** | REQ-007 (Seed-to-Shelf Traceability, QR-Code-System), REQ-016 (InvenTree-Integration fur Bestandsverwaltung), REQ-009 (ROI-Analyse, Cost-per-Gram) |
| **Abdeckungsgrad** | Minimal |

**Abdeckungsluken:** Kein Rollenkonzept (Admin/Grower/Viewer), kein Audit-Log fur Behorden, keine Kostenstellenrechnung, keine Mitarbeiterzuweisung fur Tasks.

---

#### ZG-007: Züchter / Genetik-Forscher
| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Zuchterin / Genetik-Enthusiast |
| **Profil** | Person, die neue Kreuzungen entwickelt, Phanotypen selektiert und Abstammungslinien uber mehrere Generationen dokumentiert |
| **Betriebsgrose** | 10-200 Pflanzen, Fokus auf Diversitat nicht Volumen |
| **Technische Affinitat** | Hoch |
| **Kernbedurfnis** | Genetische Abstammungslinie, Kreuzungs-Planung, Phanotyp-Selektion, Mutterpflanzenverwaltung |
| **Evidenz** | REQ-017 (Lineage-Graph, Mutterpflanzenverwaltung, PropagationBatch, Generationszahler, Retirement-Kriterien), REQ-001 (Cultivar-Entitat mit patent_status, breeder, traits) |
| **Abdeckungsgrad** | Stark |

---

## 2. Unterversorgte Nutzergruppen

### Hohes Potenzial — nicht adressiert

#### UZG-001: Lizenzierter Cannabis-Gewerbebetrieb (Compliance-Fokus)
**Profil:** Betreiber einer nach BtMG/Cannabisgesetz (DE) oder vergleichbarer Regulierung lizenzierten Anlage. Muss luckenlose Dokumentation fur Behorden-Audits vorweisen, Karenzzeiten rechtssicher nachweisen, Mitarbeiterzugriffe protokollieren und Behorden-Berichte erzeugen.
**Geschatztes Marktpotenzial:** Mit der deutschen Cannabis-Legalisierung (CanG, April 2024) und vergleichbaren Entwicklungen in der EU entsteht ein stark wachsendes Segment regulierter Kleinbetriebe. Allein in Deutschland rechnen Experten mit 50.000-100.000 Social-Club-Mitgliedern und mehreren hundert lizenzierten Anbauvereinigungen.
**Kernbedurfnis:** Audit-Trail (wer hat was wann gemacht), Karenzzeit-Compliance-Nachweis, Charge-Dokumentation fur Behorden, Rollenkonzept (nur autorisierte Personen durfen Behandlungen dokumentieren).
**Nachste bestehende Funktion:** REQ-007 Seed-to-Shelf Traceability, REQ-010 Karenzzeit (`safety_interval_days`, `requires_harvest_delay`-Edge)
**Geschatzter Anpassungsaufwand:** Mittel (Rollenkonzept + Audit-Log + Behorden-Export)

| Marktgrose | Zahlungsbereitschaft | Anpassungsaufwand | Synergie | Wachstum |
|:---:|:---:|:---:|:---:|:---:|
| 4/5 | 5/5 | 3/5 | 5/5 | 5/5 |

**Fehlende Funktionalitat:**
- JWT-Authentifizierung mit Rollenkonzept (aktuell in NFR-001 als "geplant" erwahnt, nicht implementiert)
- Immutabler Audit-Log aller Behandlungsaktionen
- Behorden-konformer Charge-Bericht (PDF-Export)
- Karenzzeit-Kalender mit Sicherheitsmargen
- 4-Augen-Prinzip fur kritische Aktionen

---

#### UZG-002: Professioneller Gewachshaus-Betrieb (Mittelbetrieb, 500-5000 Pflanzen)
**Profil:** Gewerblicher Gemuse-, Krauter- oder Blumenanbauer mit fest angestellten Mitarbeitern, mehreren Gewachshausabschnitten, standardisierten Prozessen und Vermarktungsanforderungen (Lieferscheine, Ruckverfolgbarkeit fur Lebensmittelsicherheit).
**Geschatztes Marktpotenzial:** Ca. 15.000 Gartenbaubetriebe in Deutschland laut Statistischem Bundesamt; davon wachsender Anteil an Tech-affinen Betrieben, die ERP-Systeme absetzen und spezialisierte Losungen suchen. Urban-Farming-Betriebe nehmen zu (+12% p.a. laut Marktstudie 2024).
**Kernbedurfnis:** Mehrbenutzerbetrieb mit Rollenzuweisung, standortintegrierte Aufgaben-Delegation, Ertragsberichte fur Einkaufer/Vertrieb, Substrat-Kostenrechnung, Integration mit Buchhaltungssystemen.
**Nachste bestehende Funktion:** REQ-013 (PlantingRun als Gruppencontainer), REQ-009 (Yield Analytics, Cost-per-Gram), REQ-016 (InvenTree-Integration)
**Geschatzter Anpassungsaufwand:** Hoch (Benutzer-/Rollenverwaltung ist Kernvoraussetzung)

| Marktgrose | Zahlungsbereitschaft | Anpassungsaufwand | Synergie | Wachstum |
|:---:|:---:|:---:|:---:|:---:|
| 4/5 | 4/5 | 2/5 | 4/5 | 4/5 |

**Fehlende Funktionalitat:**
- Benutzer-/Rollenverwaltung (Grower, Manager, Viewer, Buchhalter)
- Aufgaben-Delegation und -Zuweisung an Mitarbeiter
- Betriebswirtschaftliche Auswertungen (Deckungsbeitragsrechnung, Substratkosten)
- Multi-Site-Dashboard (mehrere Standorte in einer Ansicht)
- Lieferschein-/Ernte-Dokumentation fur Lebensmittelkunden

---

#### UZG-003: Zimmerpflanzen-Enthusiast / Sammlerpflanzen-Liebhaber
**Profil:** Person mit 20-200 Zimmerpflanzen (Araceae, Orchideen, Kakteen, tropische Raritaten); legt Wert auf Artenschutz, Ableger-Tausch in der Community und dokumentiert den Wuchs uber Jahre. Hat kein Agronomie-Hintergrund, aber tiefen Spezialisten-Wissen fur einzelne Gattungen.
**Geschatztes Marktpotenzial:** Pflanzenhype seit 2020; weltweit Millionen aktiver Sammler auf Instagram/Reddit/TikTok. Der globale Zimmerpflanzenmarkt (Retail) wird auf uber 20 Mrd. USD geschatzt (2024). Hohe Bereitschaft zur Nutzung digitaler Pflegetools (Planta, PictureThis haben Millionen Nutzer).
**Kernbedurfnis:** Einfache Pflegeerinnerungen (Giessen, Dunger, Umpflanzen), Fotodokumentation des Wachstums, Community-Ableger-Verwaltung, Giftigkeitshinweise fur Haustiere/Kinder.
**Nachste bestehende Funktion:** REQ-006 enthalt bereits Zimmerpflanzen-Templates (Orchidee, Kaktus, Calathea); REQ-020 Starter-Kit-System mit `toxicity_warning`-Feld
**Geschatzter Anpassungsaufwand:** Gering (Templates + vereinfachter View)

| Marktgrose | Zahlungsbereitschaft | Anpassungsaufwand | Synergie | Wachstum |
|:---:|:---:|:---:|:---:|:---:|
| 5/5 | 3/5 | 4/5 | 3/5 | 5/5 |

**Fehlende Funktionalitat:**
- Foto-Timeline pro Pflanze (Wachstumsdokumentation)
- Pflegeerinnerungen als Push-Notification (PWA-Basis in UI-NFR-012 vorhanden)
- Community-Features (Ableger-Anfragen, Tauschborsen)
- Vereinfachtes Substrat-System fur Zimmerpflanzen (Orchideeenrinde, Pon/Seramis sind explizit ausgeklammert in REQ-019 Scope-Hinweis)
- Giftigkeitsdatenbank (nur im Onboarding-Wizard angelegt, nicht systematisch ausgebaut)

---

### Mittleres Potenzial — minimal adressiert

#### UZG-004: Community-Garten / Gemeinschaftsgarten (Kollaborativer Anbau)
**Profil:** Gruppe von 5-50 Menschen, die gemeinsam einen Garten bewirtschaften. Benotigen kollaborative Aufgabenverwaltung, Anbauplatz-Zuweisung an einzelne Mitglieder und Ernte-Tracking ohne zentrale Fachperson.
**Geschatztes Marktpotenzial:** Uber 1 Million aktive Kleingarten in Deutschland; wachsendes Urban-Gardening-Segment in Stadten. Community-Garten-Bewegung wachst europaweite um ca. 8% p.a.
**Kernbedurfnis:** Mehrbenutzer ohne Fachkenntnisse, Parzellen-Verwaltung, gemeinsamer Aufgabenkalender, einfache Kommunikation.
**Nachste bestehende Funktion:** REQ-002 (Site-Hierarchie fur Parzellenstruktur), REQ-015 (Kalender fur gemeinsame Planung)
**Geschatzter Anpassungsaufwand:** Mittel

| Marktgrose | Zahlungsbereitschaft | Anpassungsaufwand | Synergie | Wachstum |
|:---:|:---:|:---:|:---:|:---:|
| 3/5 | 2/5 | 3/5 | 3/5 | 4/5 |

---

#### UZG-005: Bildungseinrichtung / Schule (Lehr-Kontext)
**Profil:** Lehrer, Ausbilder oder Hochschuldozent, der praktischen Pflanzenanbau als Unterrichtsinhalt nutzt. Benotigt Demo-Daten, klar strukturierte Lerneinheiten, Schieler-Accounts und Vergleichbarkeit der Ergebnisse.
**Geschatztes Marktpotenzial:** Ca. 33.000 allgemeinbildende Schulen in Deutschland; Schulfach "Naturwissenschaften" / "Agrarwirtschaft"; agrarwirtschaftliche Berufsschulen (ca. 500 in Deutschland).
**Kernbedurfnis:** Vordefinierte Experimente/Szenarien als Lernmaterial, Schueler-Accounts mit eingeschrankten Rechten, Vergleich von Wachstumsparametern zwischen Gruppen, Export fur Semesterberichte.
**Nachste bestehende Funktion:** REQ-021 Erfahrungsstufen (Einsteiger-Modus), REQ-011 externe Stammdaten
**Geschatzter Anpassungsaufwand:** Mittel

| Marktgrose | Zahlungsbereitschaft | Anpassungsaufwand | Synergie | Wachstum |
|:---:|:---:|:---:|:---:|:---:|
| 3/5 | 2/5 | 3/5 | 3/5 | 3/5 |

---

#### UZG-006: Aquaponik-Betreiber
**Profil:** Betreiber eines kombinierten Fisch-Pflanzen-Systems (NFT/DWC mit Fischbecken). Benotigt spezifische Wasserwerte (Ammoniak, Nitrit, Nitrat, DO), die von den Fischpflanzen-Interaktionen abhangen, sowie Fisch-Monitoring parallel zum Pflanzenmonitoring.
**Geschatztes Marktpotenzial:** Nischenmarkt mit starkem Wachstum (+20% p.a.); besonders stark in Niederlanden, UK, DACH-Raum und Nordamerika.
**Kernbedurfnis:** Aquatisches Monitoring (Ammoniak-Zyklus), Fisch-/Pflanzen-Kopplung, spezifische Dungeplanung (keine synthetischen Dunger bei Fischen).
**Nachste bestehende Funktion:** REQ-014 (Tank-Monitoring mit pH/EC/DO), REQ-019 (none-Substrat fur DWC/NFT)
**Geschatzter Anpassungsaufwand:** Hoch (eigene Fisch-Entitat notwendig)

| Marktgrose | Zahlungsbereitschaft | Anpassungsaufwand | Synergie | Wachstum |
|:---:|:---:|:---:|:---:|:---:|
| 2/5 | 3/5 | 2/5 | 3/5 | 5/5 |

---

### Langfristiges Potenzial — perspektivisch interessant

#### UZG-007: Forschungslabor / Universitat (Wissenschaftlicher Anbau)
Pflanzenwachstum als kontrolliertes Experiment. Benotigt strenge Datenintegritat, Replikation (Kontrollgruppen), statistische Auswertung, Publikations-Export. Hohe Zahlungsbereitschaft fur spezialisierte Losungen (Institutslizenz). Anpassungsaufwand hoch wegen experimenteller Metadaten-Anforderungen.

#### UZG-008: Vertikale Farm / Container Farm (Großbetrieb, industriell)
Industrieller Indoor-Anbau mit vollautomatisierter Bewasserung/Beleuchtung, Batch-Grose von 10.000+ Pflanzen, API-getriebener Betrieb ohne manuelle Eingaben, ERP-Anbindung, HACCP-Dokumentation. Architektonisch grundsatzlich kompatibel (API-First-Ansatz des Systems), aber Anpassungsaufwand extrem hoch.

#### UZG-009: Gastronomie / Farm-to-Table-Betrieb
Restaurant oder Hotel mit eigenem Krauter-/Salatanbau fur die Kuche. Benotigt Ernte-Planung nach Bedarf (Mengen-basiert statt Phasen-basiert), Lieferscheine und Verknupfung mit Rezept-Datenbank. Mittelgroszes Potenzial bei uberschaubarem Anpassungsaufwand.

---

## 3. Neue Anwendungsgebiete

### AG-001: Compliance-Management fur regulierten Anbau
**Beschreibung:** Vollstandige Dokumentationskette von der Pflanzung bis zur Ausgabe/Verteilung von Ernteprodukten, behordenkonform und audit-fahig. Abdeckt Cannabis-Anbauvereinigungen (CanG), medizinische Anbauer, perspektivisch auch biologischen Zertifizierungsanbau (Bio-Siegel).
**Relevante bestehende REQs:** REQ-007 (Seed-to-Shelf Traceability, QR-Code-System), REQ-010 (Karenzzeiten, `safety_interval_days`), REQ-013 (Batch-Tracking)
**Fehlende Funktionalitat:** JWT-Authentifizierung mit Rollenkonzept, immutabler Audit-Log, PDF-Chargenberichte, digital signierte Protokolle
**Zielgruppe:** UZG-001 (lizenzierter Cannabis-Betrieb), UZG-002 (Gewachshaus-Mittelbetrieb)
**Markttrend:** Stark wachsend (Cannabis-Legalisierung DE/EU, Bio-Zertifizierungsdruck)

---

### AG-002: Zimmerpflanzen-Pflege-App (Consumer-Segment)
**Beschreibung:** Vereinfachte Nutzungsschicht uber dem bestehenden System, die auf Zimmerpflanzen (Araceae, Orchideen, Sukkulenten, Kräuter) optimiert ist. Erforschung, Pflegeerinnerungen, Foto-Tagebuch, Community-Funktionen. Konkurrenz zu Planta, Greg, PictureThis.
**Relevante bestehende REQs:** REQ-006 (Zimmerpflanzen-Templates fur Orchidee, Kaktus, Calathea), REQ-020 (Starter-Kit-System), REQ-021 (Einsteiger-Modus), UI-NFR-009 (visuelles Design), UI-NFR-012 (PWA-Offline fur Push-Notifications)
**Fehlende Funktionalitat:** Fotodokumentation pro Pflanze, Push-Notification-basierte Pflegeerinnerungen, Giftigkeitsdatenbank, Community/Social-Features, App-Store-Prasenz (Flutter-App laut stack.md geplant aber nicht implementiert)
**Zielgruppe:** ZG-005 (Hobby-Einsteiger), UZG-003 (Zimmerpflanzen-Enthusiast)
**Markttrend:** Wachsend; Consumer-Pflanzen-Apps haben Millionen-Nutzerbasis aufgebaut

---

### AG-003: Bildungs-Modul fur Schulen und Ausbildung
**Beschreibung:** Konfigurierbare Lehr-Umgebung, in der Lehrkrafte vordefinierte Anbau-Experimente als Unterrichtsprojekte bereitstellen konnen. Schielerinnen beobachten und dokumentieren Wachstum, der Lehrer hat Uberblick uber alle Projekte.
**Relevante bestehende REQs:** REQ-001 (Botanische Stammdaten als Lernbasis), REQ-003 (Phasen fur Unterrichtsstruktur), REQ-009 (Dashboard fur Vergleichbarkeit), REQ-021 (Einsteiger-Modus)
**Fehlende Funktionalitat:** Schueler-Accounts, Kurs-Verwaltung, Export fur Unterrichtsdokumentation, vorgefertigte Lehr-Szenarien
**Zielgruppe:** UZG-005 (Bildungseinrichtungen)
**Markttrend:** Stagnierend (offentliche Bildungsbudgets); jedoch EdTech-Bereich im Aufwind fur MINT-Facher

---

### AG-004: Aquaponik-Management
**Beschreibung:** Erweiterung des bestehenden Tank- und Pflanzensystems um Fisch-Monitoring. Der Tank erhalt einen "Aquatic"-Modus, der Ammoniak-Nitrit-Nitrat-Zyklus wird uberwacht, Dungeplanung baut auf biologischer Filterleistung statt chemischer Zusatze auf.
**Relevante bestehende REQs:** REQ-014 (Tank mit DO/pH-Monitoring), REQ-005 (Sensor-Integration), REQ-004 (Dungeplanung)
**Fehlende Funktionalitat:** Fisch-Entitat (Art, Besatzdichte, Futterplan), Ammoniak-Monitoring, Aquaponik-spezifische Dungelogik (keine synthetischen Dunger), Fisch-Pflanzenverhaltnis-Berechnung
**Zielgruppe:** UZG-006 (Aquaponik-Betreiber)
**Markttrend:** Stark wachsend aber Nische

---

### AG-005: Saatgut-Bibliothek und Tauschborsen-Plattform
**Beschreibung:** Erweiterung der Cultivar-Stammdaten um Saatgut-Bestandsverwaltung, Tausch-Angebote und Community-Bewertungen von Sorten. Verbindet das bestehende Vermehrungsmanagement (REQ-017) mit sozialen Funktionen.
**Relevante bestehende REQs:** REQ-001 (Cultivar-Entitat mit Zuchterdaten), REQ-017 (PropagationBatch, Ableger-Management), REQ-016 (InvenTree fur Bestandsverwaltung)
**Fehlende Funktionalitat:** Nutzer-Saatgut-Inventar, Community-Tausch-Matching, Sorten-Bewertungen, Versand-Koordination
**Zielgruppe:** UZG-003 (Zimmerpflanzen-Enthusiast), ZG-003 (Nutzpflanzen-Gartner), ZG-007 (Zuchterin)
**Markttrend:** Nische mit loyaler Community; Monetarisierung schwierig, hoher Community-Akquisitionswert

---

## 4. Persona-Gap-Analyse

| Persona-Bedurfnis | Status | Fehlende Funktionalitat | Empfohlene REQ |
|-------------------|--------|------------------------|---------------|
| **Einfacher Einstieg (Onboarding)** | Gelb (spezifiziert, nicht fertig) | Starter-Kits nur im Wizard, keine persistierten vereinfachten Workflows | REQ-020 implementieren, Starter-Kits ausbauen |
| **Mobile Nutzung (unterwegs prufen)** | Gelb (spezifiziert) | Flutter-App noch nicht implementiert; PWA-Offline (UI-NFR-012) spezifiziert aber offen | UI-NFR-012 implementieren, Flutter-App |
| **Teamarbeit (Aufgaben delegieren)** | Rot (nicht adressiert) | Kein Rollenkonzept, keine Benutzerverwaltung, keine Task-Zuweisung an Personen | REQ-NEW: Benutzer- und Rollenverwaltung |
| **Kostenkontrolle (ROI berechnen)** | Gelb (teilweise) | REQ-009 spezifiziert "Cost-per-Gram", aber kein vollstandiges Kostenmodul; InvenTree-Integration (REQ-016) partiell | REQ-016 implementieren, Kosten-Dashboard ausbauen |
| **Wissensaufbau (lernen und optimieren)** | Gelb (spezifiziert) | Fachbegriff-Tooltips (UI-NFR-011) spezifiziert; Hilfe-Inhalte noch nicht ausgebaut | UI-NFR-011 implementieren, Glossar befallen |
| **Compliance-Nachweis (Dokumentation)** | Rot (nicht adressiert) | Kein Audit-Log, kein PDF-Export, kein Rollenkonzept | REQ-NEW: Compliance-Modul |
| **Skalierung (Betrieb vergrodern)** | Gelb (teilweise) | Multi-Site vorhanden (REQ-002), aber kein Multi-User und kein betriebswirtschaftliches Reporting | Rollenkonzept + erweitertes Reporting |
| **Community (Austausch, Tipps)** | Rot (nicht adressiert) | Keine Community-Features, keine Verknupfung mit externen Plattformen | REQ-NEW: Community-Funktionen (langfristig) |
| **Foto-Dokumentation** | Rot (nicht adressiert) | Kein Foto-Upload, keine Foto-Timeline pro Pflanze | REQ-NEW: Foto-Tagebuch |
| **Push-Benachrichtigungen** | Gelb (PWA-Basis) | UI-NFR-012 schafft technische Grundlage; Notification-Logik fehlt | UI-NFR-012 + Notification-Service |
| **Offline-Nutzung (Growroom/Keller)** | Gelb (spezifiziert) | UI-NFR-012 spezifiziert, Service-Worker noch nicht implementiert | UI-NFR-012 implementieren |
| **Kiosk-Bedienung (verschmutzte Hande)** | Gelb (spezifiziert) | UI-NFR-011 Kiosk-Modus vollstandig spezifiziert, Implementierung offen | UI-NFR-011 Kiosk implementieren |

**Legende:** Rot = nicht adressiert | Gelb = spezifiziert, nicht implementiert | Grun = implementiert

---

## 5. Anwendungsgebiet x Zielgruppen-Matrix

|  | ZG-001 Indoor-Grower | ZG-002 Cannabis | ZG-003 Gemuse/Krauter | ZG-004 SysAdmin | ZG-005 Einsteiger | ZG-006 Mikro-Farm | ZG-007 Zuchterin | UZG-001 Compliance | UZG-002 Gewachshaus | UZG-003 Zimmerpflanze |
|--|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Lifecycle Management** | Vollst | Vollst | Vollst | Vollst | Anpassbar | Anpassbar | Vollst | Anpassbar | Anpassbar | Nicht |
| **Nahrstoffmanagement** | Vollst | Vollst | Anpassbar | Vollst | Nicht | Anpassbar | Anpassbar | Anpassbar | Anpassbar | Nicht |
| **Umgebungssteuerung** | Vollst | Vollst | Anpassbar | Vollst | Nicht | Anpassbar | Nicht | Anpassbar | Anpassbar | Nicht |
| **Qualitatssicherung / Ernte** | Vollst | Vollst | Vollst | Vollst | Anpassbar | Anpassbar | Vollst | Anpassbar | Anpassbar | Nicht |
| **Compliance & Audit** | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht |
| **Supply Chain / Inventar** | Anpassbar | Anpassbar | Anpassbar | Vollst | Nicht | Anpassbar | Nicht | Anpassbar | Anpassbar | Nicht |
| **Wissensmanagement / Stammdaten** | Vollst | Vollst | Vollst | Vollst | Anpassbar | Anpassbar | Vollst | Vollst | Vollst | Anpassbar |
| **Planung & Scheduling** | Vollst | Vollst | Vollst | Vollst | Anpassbar | Anpassbar | Anpassbar | Anpassbar | Anpassbar | Nicht |
| **Vermehrung / Genetik** | Vollst | Vollst | Anpassbar | Anpassbar | Nicht | Nicht | Vollst | Vollst | Anpassbar | Nicht |
| **Schutzmastnahmen (IPM)** | Vollst | Vollst | Vollst | Vollst | Anpassbar | Anpassbar | Anpassbar | Anpassbar | Vollst | Nicht |
| **Foto-Dokumentation** | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht |
| **Community / Tausch** | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht |
| **Teamarbeit / Rollen** | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht | Nicht |

**Legende:** Vollst = vollstandig adressiert | Anpassbar = teilweise / mit geringem Aufwand anpassbar | Nicht = nicht adressiert

---

## 6. Empfehlungen

### Sofort umsetzbar (Quick Wins, minimaler Entwicklungsaufwand)

**QW-001: Zimmerpflanzen-Starter-Kits ausbauen**
Zielgruppe: UZG-003 (Zimmerpflanzen-Enthusiast), ZG-005 (Einsteiger)
REQ-020 enthalt bereits die `toxicity_warning`-Struktur und das Starter-Kit-System. Die vier Zimmerpflanzen-Templates aus REQ-006 (Orchidee, Kaktus, Calathea, Tropische Grunpflanze) als vollstandige Starter-Kits verpacken und im Onboarding-Wizard verfugbar machen. Kostenpunkt: 2-3 Entwicklertage fur Backend-Seed-Daten und Wizard-Erweiterung.
Erwarteter Nutzen: Erschliessing eines Millionensegments, das aktuell nicht erkannt wird, mit marginalen Erweiterungen.

**QW-002: REQ-019 Zimmerpflanzen-Substrate erganzen**
Zielgruppe: UZG-003
REQ-019 schlieSt explizit Orchideeenrinde, Pon/Seramis, Sphagnum aus dem Primdrfokus aus (Scope-Hinweis). Diese als vollwertige Substrattypen aufnehmen, da die Zimmerpflanzen-Zielgruppe dies zwingend benotigt. Aufwand: 1 Entwicklertag (Enum-Erweiterung).

**QW-003: Giftigkeitsdatenbank als eigenstandige Entitat ausbauen**
Zielgruppe: UZG-003, ZG-005
Das `toxicity_warning`-Feld in REQ-020 ist ein Attribut des Starter-Kits. Als eigenstandige `Toxicity`-Entitat mit standardisierten Kategorien (ASPCA-Klassifikation) pro Species/BotanicalFamily modelliern. Integriert in die Arten-Suche und das Dashboard. Aufwand: 2-3 Entwicklertage.

**QW-004: Kiosk-Modus und PWA implementieren**
Zielgruppe: ZG-001, ZG-002, ZG-006
UI-NFR-011 (Kiosk) und UI-NFR-012 (PWA) sind vollstandig spezifiziert aber nicht implementiert. Ohne diese bleiben mobile Nutzungsszenarien im Growroom unrealisiert. Kiosk-Modus ist der grostmogliche Quick Win fur bestehende Zielgruppen ohne neue Funktionalitat.

---

### Mittelfristig (Nachste Entwicklungsphase, 1-3 Monate)

**MT-001: JWT-Authentifizierung und Rollenkonzept implementieren**
Zielgruppe: UZG-001 (Compliance), UZG-002 (Gewachshaus-Betrieb), UZG-004 (Community-Garten)
Voraussetzung fur alle Mehrbenutzer-Szenarien. NFR-001 erwahnt JWT-Auth als geplant. Mindestens drei Rollen: Admin (alles), Grower (eigene Pflanzen + Tasks), Viewer (Lesezugriff). Anschliestend Task-Zuweisung an Nutzer ermoglichen (REQ-006 erganzen).
Erwarteter Nutzen: Offnet das System fur Teambetrieb; Grundvoraussetzung fur die Hochwertigsten Zielgruppen (UZG-001, UZG-002).

**MT-002: Compliance-Audit-Log (Append-Only)**
Zielgruppe: UZG-001 (Compliance)
Immutabler Log aller behandlungsrelevanter Aktionen (Dungerausbringung, IPM-Behandlungen, Phasentransitionen) mit Nutzer-Referenz und Zeitstempel. Basis fur behordenkonforme Dokumentation. Aufbauend auf MT-001 (JWT-Auth).

**MT-003: Erweitertes Foto-Dokumentationsmodul**
Zielgruppe: UZG-003 (Zimmerpflanze), ZG-001-003 (alle Grower), ZG-007 (Zuchterin)
Foto-Upload pro Pflanze/Behandlung/Beobachtung mit Timeline-View. Direkte Verknupfung mit IPM-Inspektionen (Befallsfoto) und Phasentransitionen (Wachstumsfoto). Technisch: S3-kompatibler Objektspeicher, Thumbnail-Generierung. Hohes Nutzerwert-zu-Aufwand-Verhaltnis.

**MT-004: Betriebswirtschaftliches Basis-Modul**
Zielgruppe: UZG-002 (Gewachshaus-Betrieb), ZG-006 (Mikro-Farm)
Erweiterung von REQ-009 (Dashboard) um Kostenstellenrechnung: Dungerkosten pro Batch, Energiekosten pro Watt (REQ-018), Substratkosten (REQ-019), Ertrag pro m² und ROI-Berechnung. Grunddaten sind im System vorhanden; es fehlt die aggregierende Berechnungsschicht.

---

### Langfristig / Strategisch

**LF-001: Flutter-Mobile-App fertigstellen**
Laut stack.md geplant aber "not yet implemented". Mobile ist die primare Nutzungsschicht fur Kiosk-/Growroom-Szenarien. Die PWA (UI-NFR-012) ist ein Zwischenschritt. Eine native Flutter-App erschlieSt den App-Store-Kanal und ermoglicht Push-Notifications (Pflege-Erinnerungen fur UZG-003 Zimmerpflanzen-Zielgruppe).

**LF-002: Compliance-Exportmodul fur regulierten Cannabis-Anbau**
PDF-generierter Chargenbericht nach Vorlage des Cannabisgesetzes (DE). QR-Code-System (in REQ-007 bereits spezifiziert) als Standard-Komponente fur alle Chargen aktivieren. Marktpotenzial sehr hoch bei niedrigem Wettbewerb in diesem spezifischen Nischensegment.

**LF-003: Community-Plattform / Social Features**
Saatgut-/Ableger-Tauschborse, Sortenratings, offene Kulturdatenblattetausche. Langfristiger Netzwerkeffekt: je mehr Nutzer, desto besser die Stammdaten (Companion-Planting-Bewertungen, Ertragsdaten fur ML-Prognosen). Aufwand sehr hoch; strategisch wertvoll fur Marktpositionierung.

**LF-004: Aquaponik-Erweiterung**
Fisch-Entitat, Ammoniak-Zyklus-Monitoring, organisch-biologische Dungeplanung. Starkes Differenzierungsmerkmal gegenuber bestehenden Pflanzenverwaltungslosungen. Aquaponik-Markt wachst stark.

---

## 7. Prioritats-Ranking: Neue Zielgruppen

| Rang | Zielgruppe | Gesamtscore | Empfehlung | Zeitraum |
|------|-----------|-------------|-----------|---------|
| 1 | UZG-003 Zimmerpflanzen-Enthusiast | 4/5 | Sofort adressieren (Quick Wins QW-001 bis QW-003) | 1-4 Wochen |
| 2 | UZG-001 Lizenzierter Cannabis-Betrieb | 4,4/5 | Mittelfristig, Voraussetzung JWT-Auth | 2-4 Monate |
| 3 | UZG-002 Gewachshaus-Mittelbetrieb | 3,6/5 | Mittelfristig nach Rollenkonzept | 3-6 Monate |
| 4 | UZG-004 Community-Garten | 3/5 | Mittelfristig, nach Rollenkonzept | 3-6 Monate |
| 5 | UZG-005 Bildungseinrichtung | 2,8/5 | Langfristig, nach Community-Features | 6-12 Monate |
| 6 | UZG-006 Aquaponik | 3/5 | Langfristig, eigenstandiges Erweiterungsmodul | 9-18 Monate |
| 7 | UZG-007 Forschungslabor | 2,5/5 | Perspektivisch, Enterprise-Segment | 12+ Monate |
| 8 | UZG-008 Industrielle Vertikalfarm | 2/5 | Nicht empfohlen fur aktuellen Entwicklungsstand | — |

---

## 8. Strategischer Hinweis

Das System steht vor einer Positionierungs-Entscheidung: Es kann entweder als **Profi-Tool fur erfahrene Grower** (Cannabis, Hydroponik, Automatisierung) weiterentwickelt werden — mit hoher Zahlungsbereitschaft, aber kleinem Markt — oder als **Plattform fur alle Pflanzenliebhaber** mit einem Consumer-Einstieg (Zimmerpflanzen-App) und einem professionellen Upscaling-Pfad.

Die aktuelle Architektur (generische Entitatsmodelle, Erfahrungsstufen-System REQ-021, Onboarding-Wizard REQ-020) legt nahe, dass die Plattform-Strategie bereits beabsichtigt ist. Drei konkrete strategische Hinweise:

**1. Zimmerpflanzen als Akquisitionskanal.** Der Zimmerpflanzen-Markt ist riesig, die Hurde fur einen "Kamerplanter Lite"-Einstieg ist gering (REQ-006 Templates sind bereits vorhanden), und Zimmerpflanzen-Nutzer konvertieren organisch zu Gemuse-/Krauteranbau. Das System hat den technischen Unterbau; es fehlt nur die Verpackung.

**2. Compliance als Premiumsegment.** Mit der Cannabis-Legalisierung entsteht ein regulierter Markt mit zwingenden Dokumentationspflichten und hoher Zahlungsbereitschaft. Kamerplanter hat mit Seed-to-Shelf-Traceability und Karenzzeit-Tracking bereits die Fachlichkeit; ein Compliance-Modul ware ein starkes Differenzierungsmerkmal mit echtem Wettbewerbsvorteil.

**3. Das fehlende Rollenkonzept ist der kritische Pfad.** Fast alle unterversorgten Zielgruppen (UZG-001 bis UZG-004) benotigen Mehrbenutzer-Funktionalitat. Die Implementierung von JWT-Auth und einem einfachen Rollenmodell ist die einzige Masynahme, die gleichzeitig vier neue Zielgruppen erschliesyt. Solange dieses Feature fehlt, bleibt Kamerplanter ein Ein-Personen-Tool — unabhangig von allen anderen Weiterentwicklungen.
