# Zielgruppen- und Anwendungsgebietsanalyse

**Erstellt von:** Zielgruppen-Analyst (Subagent)
**Datum:** 2026-03-21
**Analysierte Dokumente:** 28 funktionale Anforderungen (REQ-001 bis REQ-028 inkl. REQ-004-A und REQ-015-A) + 11 nicht-funktionale Anforderungen (NFR-001 bis NFR-011) + spec/stack.md
**Methodik:** Implizite/Explizite Signalextraktion aus Anforderungsdokumenten, Jobs-to-be-Done-Mapping, Markt-Gap-Analyse nach Betriebstyp, Domäne, Rolle und Nutzungskontext

---

## Executive Summary

Kamerplanter adressiert aktuell drei klar abgrenzbare Primärzielgruppen stark: den ambitionierten Cannabis-Indoor-Grower, den Freilandgärtner mit Gemüsegarten sowie den Zimmerpflanzen-Enthusiasten. Das System ist technisch bemerkenswert breit aufgestellt (Hydroponik, Freiland, Aquaponik, Smart-Home-Integration, Multi-Tenancy, DSGVO) und geht damit weit über ein reines Hobby-Tool hinaus. Die kritischsten Lücken liegen bei drei Gruppen mit hohem Marktwachstum: (1) Casual-Hobby-Nutzer ohne botanisches Vorwissen, die einen foto-basierten Pflanzenidentifikations-Einstieg erwarten; (2) gewerbliche Mikro- und Kleinstbetriebe (Urban Farms, Marktgärtnereien, CSA-Betriebe), die Kosten-Controlling und Ertragsdokumentation auf betriebswirtschaftlichem Niveau benötigen; und (3) Bildungseinrichtungen und Forschungslabore, die reproduzierbare Protokolle und Datenexport-Schnittstellen für wissenschaftliche Auswertungen brauchen. Die größte strategische Chance liegt in der Kombination aus Light-Modus (REQ-027) und einem einfachen KI-Bilderkennungs-Onboarding: Diese Verbindung erschließt den massenmarktfähigen Segment der Casual User, ohne das bestehende Expertensystem anzutasten.

---

## 1. Aktuell adressierte Nutzergruppen

### Primäre Zielgruppen (stark adressiert)

#### ZG-001: Ambitionierter Cannabis Indoor Grower

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Cannabis Indoor Grower (Heimanbau bis Semi-Professionell) |
| **Profil** | Erfahrener Anbauer, 25-45 Jahre, technisch affin. Betreibt ein bis mehrere Growzelte, arbeitet mit Hydro/Coco-Substraten, hat Interesse an EC-Optimierung, Trichom-Reife, Strain-Genetik und lückenloser Dokumentation (ggf. zur eigenen Rechtssicherheit nach CanG-Liberalisierung). |
| **Betriebsgröße** | 4-50 Pflanzen, 1-3 Growzelte oder ein Indoor-Raum |
| **Technische Affinität** | Hoch |
| **Kernbedürfnis** | Maximale Kontrolle über Wachstumsparameter, lückenlose Dokumentation, optimaler Erntezeitpunkt durch Trichom-Monitoring, genetische Rückverfolgbarkeit von Klonen |
| **Evidenz** | REQ-003 (Phasensteuerung: 12/12-Trigger, Autoflower-Sonderlogik), REQ-004 (EC-Budget, CalMag-Korrektur, Multi-Part-Dünger, Mischsequenz-Validierung), REQ-007 (Trichom-Mikroskopie, Pistil-Färbung, Dark-Period), REQ-008 (Jar-Curing, Burping-Schedule), REQ-010 (Hermaphrodismus-Protokoll, Wirkstoff-Rotation), REQ-013 (Clone-Run, Mutterpflanzen-Verwaltung), REQ-017 (Genetische Linie, klonale Generation), REQ-011 (Otreeba-Adapter für Cannabis-Sorten), NFR-011 (CanG-Aufbewahrungsfristen) |
| **Abdeckungsgrad** | Vollständig - diese Gruppe ist die originäre Designzielgruppe |

#### ZG-002: Freilandgärtner / Gemüsegärtner

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Hobby-Freilandgärtner mit Gemüse- und Kräutergarten |
| **Profil** | Gartenbesitzer mit eigenem Beet oder Parzelle, 35-65 Jahre, mittlere bis hohe Gartenerfahrung. Sät selbst aus, kompostiert, arbeitet mit organischen Düngern, plant Fruchtfolgen. Hat Interesse an Aussaatkalender, Mischkultur und saisonaler Organisation. |
| **Betriebsgröße** | 20-200 Pflanzen, 1-5 Beete, 10-100 m² |
| **Technische Affinität** | Gering bis Mittel |
| **Kernbedürfnis** | Strukturierter Aussaatkalender, Fruchtfolge-Tracking, Mischkultur-Empfehlungen, saisonale Erinnerungen, Überwinterungsmanagement |
| **Evidenz** | REQ-001 (Freiland-Felder: frost_sensitivity, sowing_dates, harvest_months), REQ-002 (Beetplanung, Fruchtfolge, Wasserquellen-Konfiguration), REQ-004 (Organische Freiland-Düngung: g/m², Jauchen), REQ-006 (Outdoor-Templates: Frostschutz, Obstbaum-Schnitt, Abhärtungs-Workflow), REQ-013 (Sukzessions-Aussaat), REQ-015 (Aussaatkalender-Modus, Saisonübersicht), REQ-022 (Überwinterungsmanagement, Winterhärte-Ampel, Knollen-Zyklus), REQ-028 (Mischkultur-Engine) |
| **Abdeckungsgrad** | Vollständig - durch Outdoor-Garden-Planner Review systematisch erweitert |

#### ZG-003: Zimmerpflanzen-Enthusiast

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Zimmerpflanzen-Liebhaber (Casual bis Sammler) |
| **Profil** | Stadtwohnung oder Haus, 5-80 Zimmerpflanzen, breite Altersgruppe. Interessiert an Pflege-Erinnerungen, artspezifischen Gießintervallen und Vermehrung. Kennt die meisten Pflanzennamen, benötigt aber Unterstützung bei Substrat-Wahl, Überwinterung und Schädlingserkennung. |
| **Betriebsgröße** | 5-80 Pflanzen, Wohnung/Haus |
| **Technische Affinität** | Gering bis Mittel |
| **Kernbedürfnis** | Einfache Pflege-Erinnerungen mit Ein-Tap-Bestätigung, artspezifische Gießmethoden, saisonale Dormanz-Hinweise, Vermehrungsunterstützung für Zimmerpflanzen |
| **Evidenz** | REQ-022 (9 Care-Style-Presets: tropical, succulent, orchid, calathea etc., Gießmethoden-Anleitung), REQ-017 (Blattsteckling, Teilung, Wasser-Bewurzelung, Kindel/Ableger), REQ-003 (Perenniale Zimmerpflanze: Aktiv/Dormanz-Zyklus), REQ-019 (orchid_bark, pon_mineral, sphagnum Substrattypen), REQ-021 (Einsteiger-Modus mit Progressive Disclosure), REQ-020 (Onboarding-Wizard, Starter-Kits), REQ-027 (Light-Modus: Einzelnutzer ohne Login) |
| **Abdeckungsgrad** | Vollständig auf Funktionsebene - Onboarding-Barrieren bleiben (kein Foto-Einstieg) |

### Sekundäre Zielgruppen (teilweise adressiert)

#### ZG-004: Gemeinschaftsgarten-Mitglied / Urban Gardener

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Gemeinschaftsgarten-Nutzer (Mitglied oder Admin) |
| **Profil** | Mitglied in einem Gemeinschaftsgarten, Urban-Farming-Projekt oder CSA. Teilt Fläche mit anderen, koordiniert Aufgaben, organisiert Ernte-Tausch. Nutzt gemeinsame Bestelllisten und Pinnwand. |
| **Betriebsgröße** | 1-5 eigene Parzellen, 5-50 Mitglieder im Tenant |
| **Technische Affinität** | Gering bis Mittel |
| **Kernbedürfnis** | Aufgabendelegation, Gießdienst-Rotation, gemeinsame Einkaufsliste, Pinnwand für Koordination |
| **Evidenz** | REQ-024 (Tenant-Typ organization, DutyRotation, BulletinPost, SharedShoppingList, Einladungslink), REQ-006 (Aufgaben-Zuweisung an Mitglieder), REQ-002 (Location-Assignment per Mitglied) |
| **Abdeckungsgrad** | Teilweise - Kollaborations-Features noch nicht vollständig implementiert (REQ-024 v1.4 RBAC ausstehend) |

#### ZG-005: Cannabis Social Club / Anbauvereinigung

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Organisierter Cannabis-Anbauverein (CanG-konform) |
| **Profil** | Eingetragener Verein oder Social Club nach CanG, 10-500 Mitglieder. Muss Anbauprotokolle, Ernte-Dokumentation und Abgabe-Nachweise für Behörden führen. Nutzt OIDC für Mitglieder-SSO. |
| **Betriebsgröße** | 20-500 Pflanzen, mehrere Räume, Team-Betrieb |
| **Technische Affinität** | Mittel bis Hoch |
| **Kernbedürfnis** | Compliance-Dokumentation nach CanG, revisionssichere Aufbewahrung, RBAC für Rollen-Trennung (Anbauer/Manager/Buchhalter), OIDC-Integration für Vereins-IdP |
| **Evidenz** | NFR-011 (CanG-Aufbewahrungsfristen), REQ-023 (OIDC-Anbindung, Service Accounts), REQ-024 (RBAC Permission-Matrix, Multi-Tenant), REQ-025 (DSGVO-Betroffenenrechte), REQ-013 (Seed-to-Shelf-Traceability) |
| **Abdeckungsgrad** | Teilweise - Compliance-Reporting fehlt als eigenständige Funktion |

#### ZG-006: Hydroponik- und Vertical-Farming-Betreiber

| Dimension | Beschreibung |
|-----------|-------------|
| **Bezeichnung** | Semi-professioneller Hydroponik-Betreiber / Urban Farm |
| **Profil** | Betreibt NFT, DWC, Aeroponik oder Ebb-and-Flow in einem Kellerraum, Container oder kleinen Gewächshaus. Produziert Kräuter, Salat oder Microgreens für Eigenverbrauch oder lokalen Verkauf. Investiert in Sensoren und Automatisierung. |
| **Betriebsgröße** | 50-500 Pflanzen, 1-3 Systeme, vollautomatische Bewässerung |
| **Technische Affinität** | Hoch |
| **Kernbedürfnis** | Tank-Management, EC/pH-Automatisierung via Home Assistant, Ernteplanung mit Yield-Tracking, Kostenkontrolle pro Gram |
| **Evidenz** | REQ-014 (Tank-Typen inkl. NFT, DWC, Rezirkulation, Stammlösung), REQ-018 (VPD-Regelkreis, Hysterese, Phase-Profile), REQ-005 (HA-Integration, MQTT), REQ-009 (Resource Dashboard: Cost per Gram, kWh-Tracking) |
| **Abdeckungsgrad** | Teilweise - Dashboard und Kostenanalyse noch nicht implementiert |

---

## 2. Unterversorgte Nutzergruppen

### Hohes Potenzial - nicht adressiert

#### UZG-001: Casual Hobby-Nutzer (Pflanzennamen unbekannt)

**Profil:** Jüngere Zielgruppe (20-35 Jahre), kauft Pflanzen im Supermarkt oder Baumarkt ohne Etikett, kennt die Art oft nicht, ist aber motiviert die Pflanze am Leben zu erhalten. Erwartet Foto-basierte Identifikation als Einstiegspunkt.

**Geschätztes Marktpotenzial:** Sehr groß - dies ist das massenmarktfähige Segment. Allein in Deutschland haben schätzungsweise 15-20 Millionen Haushalte Zimmerpflanzen. Apps wie PictureThis, PlantNet und Planta haben gemeinsam über 100 Millionen Downloads.

**Kernbedürfnis:** Pflanze fotografieren, Namen erhalten, sofortige Pflegeanleitung bekommen - alles ohne botanisches Vorwissen.

**Nächste bestehende Funktion:** REQ-021 Beginner-Modus, REQ-020 Onboarding-Wizard, REQ-022 Pflegeerinnerungen. Fehlt: Foto-basierte Artbestimmung als Onboarding-Schritt.

**Geschätzter Anpassungsaufwand:** Mittel (KI-Bilderkennungs-API-Integration als neuer Adapter im REQ-011-Muster)

**Bewertung:**

| Marktgröße | Zahlungsbereitschaft | Anpassungsaufwand | Synergie | Wachstum |
|:---:|:---:|:---:|:---:|:---:|
| 5/5 | 2/5 | 3/5 | 5/5 | 5/5 |

**Hinweis:** Bereits als N-001 in der MEMORY.md als "Dealbreaker für Casual User" identifiziert und mit KI-Integration als erstem Feature priorisiert.

---

#### UZG-002: Marktgärtner / CSA-Betrieb / Mikro-Farm

**Profil:** Kleinbetrieb mit 0,1-2 ha, produziert für Wochenmarkt, Abo-Kiste oder Restaurant-Direktlieferung. Braucht Anbauplanung mit Flächenbelegung, Ertragsprognose für Bestellplanung, einfache Buchführung für Betriebsmittelkosten und Deckungsbeitragsrechnung pro Kultur.

**Geschätztes Marktpotenzial:** Wachsendes Segment. Urban Farming, Permakultur-Betriebe und CSA-Konzepte wachsen europaweit 15-20% jährlich. In Deutschland gibt es schätzungsweise 8.000-12.000 Kleinstbetriebe mit gewerblicher Direktvermarktung.

**Kernbedürfnis:** Flächenplanung (welche Kultur wann auf welche Fläche?), Mengenplanung (wann ist wie viel erntereif?), Deckungsbeitragsrechnung (lohnt sich Kultur X?), einfache Buchführung für Betriebsmittelverbrauch.

**Nächste bestehende Funktion:** REQ-002 (Beetplanung, Flächenverwaltung), REQ-013 (Pflanzdurchlauf mit Batch), REQ-007 (Ernte-Dokumentation), REQ-009 (Harvest Dashboard mit Yield Analytics). Fehlt: Flächenbelegungsplan (Gantt pro Beet), Preiskalkulation, Abo-Kisten-Integration, Lieferplanung.

**Geschätzter Anpassungsaufwand:** Hoch (neue REQs für Betriebswirtschaft notwendig)

**Bewertung:**

| Marktgröße | Zahlungsbereitschaft | Anpassungsaufwand | Synergie | Wachstum |
|:---:|:---:|:---:|:---:|:---:|
| 3/5 | 5/5 | 2/5 | 4/5 | 4/5 |

---

#### UZG-003: Bildungseinrichtungen (Schule, Berufsschule, Uni-Lehr-Gewächshaus)

**Profil:** Biologielehrer, Berufsschul-Gärtner, Hochschul-Botanik-Department. Betreiben ein oder mehrere Lehr-Gewächshäuser oder Schulgärten mit wechselnden Nutzergruppen (Schulklassen, Semester-Gruppen). Brauchen reproduzierbare Protokolle, Vergleichs-Dokumentation über Kohorten und Datenexport für Lernerfolgsmessung.

**Geschätztes Marktpotenzial:** Mittelgroß aber strategisch wertvoll als Multiplikator. Allein in Deutschland gibt es ca. 40.000 allgemeinbildende Schulen und mehrere tausend gartenbauliche Berufsschulen und Fachhochschulen.

**Kernbedürfnis:** Mehrbenutzerbetrieb mit Gruppen (Schulklassen als Sub-Tenants), reproduzierbare Versuchsprotokolle, Datenexport (CSV/JSON) für Unterrichtsauswertung, einfache Dashboards für Schüler-Präsentationen.

**Nächste bestehende Funktion:** REQ-024 (Multi-Tenant, Einladungslink), REQ-009 (Dashboard), REQ-012 (CSV-Import). Fehlt: Gruppen-/Klassen-Verwaltung innerhalb eines Tenants, Datenexport für Unterrichtszwecke, vereinfachte Lernansicht.

**Geschätzter Anpassungsaufwand:** Mittel (Nutzung bestehender Multi-Tenant-Infrastruktur, neue UI-Templates)

**Bewertung:**

| Marktgröße | Zahlungsbereitschaft | Anpassungsaufwand | Synergie | Wachstum |
|:---:|:---:|:---:|:---:|:---:|
| 3/5 | 3/5 | 3/5 | 4/5 | 3/5 |

---

### Mittleres Potenzial - minimal adressiert

#### UZG-004: Orchideen-/Bromelien-/Kakteen-Sammler (Spezialsammlung)

**Profil:** Leidenschaftlicher Pflanzensammler mit 50-500 Exemplaren einer oder weniger Pflanzengattungen. Kennt die Botanik sehr gut, dokumentiert akribisch. Braucht artspezifisch differenzierte Pflegepläne, Herkunfts-Tracking (Wildsammlung, Kulturlinie), Blüte-Tracking und Community-Sharing.

**Geschätztes Marktpotenzial:** Mittelgroß mit hoher Zahlungsbereitschaft. Orchideen-Gesellschaften, Kakteen-Freunde und Bromelien-Clubs haben in Europa je mehrere tausend aktive Mitglieder. Diese Gruppe kauft teure Spezialpflanzen und teure Spezial-Tools.

**Kernbedürfnis:** Herkunfts-Dokumentation (Importnachweis für CITES-Pflanzen), Blüte-Kalender, Kreuzungs-Dokumentation, Tausch-/Verkauf-Funktionen zwischen Sammlern.

**Nächste bestehende Funktion:** REQ-017 (Genetische Linie, Vermehrung), REQ-003 (Perenniale Zyklen), REQ-022 (Orchideen-Preset). Fehlt: CITES-Dokumentation, Blüte-Kalender als eigenständige View, Community-Tauschbörse.

**Geschätzter Anpassungsaufwand:** Gering bis Mittel (Erweiterung bestehender Stammdaten, neue Edge-Typen)

**Bewertung:**

| Marktgröße | Zahlungsbereitschaft | Anpassungsaufwand | Synergie | Wachstum |
|:---:|:---:|:---:|:---:|:---:|
| 2/5 | 5/5 | 4/5 | 4/5 | 3/5 |

---

#### UZG-005: Professioneller Gewächshaus-Betrieb (Zierpflanzen-Produktion)

**Profil:** Blumenhandel, Gärtnerei oder Baumschule mit gewerblicher Zierpflanzen-Produktion. 500-10.000 Pflanzen, mehrere Mitarbeiter, EC/pH-Automatisierung via Bewässerungscomputer. Braucht Chargen-Management, Lieferschein-Dokumentation und Compliance.

**Geschätztes Marktpotenzial:** Groß aber schwer zugänglich (etablierte Branchensoftware wie Hortisystems, GABOT dominieren). Mittelfristig erreichbar über Open-Source-Strategie.

**Kernbedürfnis:** Chargen-Management (Anzucht→Produktion→Verkauf), Pflanzenpässe (EU-Pflanzenschutz-Verordnung), Lieferscheine, Integration mit Warenwirtschaft.

**Nächste bestehende Funktion:** REQ-013 (Batch-Operationen), REQ-016 (InvenTree-Integration), REQ-023 (Service Accounts). Fehlt: Pflanzenpässe, Lieferscheine, EAN-Barcodes, Warenwirtschafts-Integration.

**Geschätzter Anpassungsaufwand:** Sehr hoch (neue Domäne: Betriebswirtschaft, Regulatorik)

**Bewertung:**

| Marktgröße | Zahlungsbereitschaft | Anpassungsaufwand | Synergie | Wachstum |
|:---:|:---:|:---:|:---:|:---:|
| 4/5 | 5/5 | 1/5 | 3/5 | 2/5 |

---

#### UZG-006: Kräuter- und Microgreens-Produzent (Gastronomie-Belieferung)

**Profil:** Kleinstbetrieb oder Hobby-Profi, der frische Kräuter oder Microgreens für Restaurants, Cafés oder Lieferdienste produziert. Typischerweise in einem umgebauten Keller oder Container, mit mehreren LED-Ebenen und Hydroponik-System. Braucht präzise Ernte-Planung für just-in-time-Lieferung.

**Geschätztes Marktpotenzial:** Wachsend. Microgreens als Trend in der Gastronomie seit 2018 konstant wachsend. Viele Kleinstproduzenten suchen günstige Planungs-Software.

**Kernbedürfnis:** Ernte-Terminplanung rückwärts aus Lieferterminen, Batch-Rotation (immer eine Ernte bereit), Kunden-Verwaltung (Wer bekommt wieviel?), Einfache Abrechnung.

**Nächste bestehende Funktion:** REQ-013 (Sukzessions-Aussaat), REQ-007 (Ernte-Management), REQ-015 (Kalenderansicht). Fehlt: Rückwärts-Planung aus Liefertermin, Kunden-CRM, Abrechnungs-Export.

**Geschätzter Anpassungsaufwand:** Mittel

**Bewertung:**

| Marktgröße | Zahlungsbereitschaft | Anpassungsaufwand | Synergie | Wachstum |
|:---:|:---:|:---:|:---:|:---:|
| 3/5 | 4/5 | 3/5 | 5/5 | 4/5 |

---

### Langfristiges Potenzial - perspektivisch interessant

#### UZG-007: Forschungslabore / Phytobiologie-Studiengruppen

Wissenschaftliche Einrichtungen mit kontrollierten Anbaukammern (Klimaschränke, Pflanzenwachstumsschränke). Brauchen exakten Datenexport (TimescaleDB-Zeitreihen), Versuchsdesign-Protokolle und reproduzierbare Bedingungen. Hohes Prestige als Referenzkunde, aber sehr spezialisierte Anforderungen (z.B. Nacht-unterbrochene Lichtperioden, präzise GDD-Kalibrierung).

| Marktgröße | Zahlungsbereitschaft | Anpassungsaufwand | Synergie | Wachstum |
|:---:|:---:|:---:|:---:|:---:|
| 1/5 | 5/5 | 2/5 | 4/5 | 3/5 |

#### UZG-008: Aquaponik-Hobbyist / Semi-Professioneller Aquaponiker

Direkt adressiert durch REQ-026, aber noch nicht implementiert. Potenziell attraktive Nische: Aquaponik-Einsteiger-Kits (Tilapia + Salat) wachsen als Heimautomatisierungs-Trend. Kamerplanter ist bereits gut positioniert durch REQ-026 (Stickstoffkreislauf, Biofilter-Management).

| Marktgröße | Zahlungsbereitschaft | Anpassungsaufwand | Synergie | Wachstum |
|:---:|:---:|:---:|:---:|:---:|
| 2/5 | 3/5 | 4/5 | 5/5 | 4/5 |

#### UZG-009: Permakultur-Praktiker / Food-Forest-Planer

Betreiber eines Permakultur-Gartens oder Food-Forest mit Schwerpunkt auf mehrjährigen Pflanzen-Kombinationen, Guild-Planung und minimaler Intervention. Die bestehende Mischkultur-Engine (REQ-028) und Fruchtfolge-Verwaltung (REQ-002) sind gute Grundlagen, aber es fehlen mehrjährige Guild-Strukturen und Sukzessions-Ökologie.

| Marktgröße | Zahlungsbereitschaft | Anpassungsaufwand | Synergie | Wachstum |
|:---:|:---:|:---:|:---:|:---:|
| 2/5 | 2/5 | 2/5 | 4/5 | 3/5 |

---

## 3. Neue Anwendungsgebiete

### AG-001: KI-gestützte Pflanzenidentifikation (Foto-Onboarding)

**Beschreibung:** Foto-basierte Artbestimmung als Einstiegspunkt für Casual User. Nutzer fotografiert eine unbekannte Pflanze, das System identifiziert die Art, schlägt die passenden Species-Stammdaten vor und legt das CareProfile automatisch an.

**Relevante bestehende REQs:** REQ-011 (Adapter-Pattern für externe APIs), REQ-020 (Onboarding-Wizard), REQ-021 (Beginner-Modus), REQ-022 (Care-Style-Presets)

**Fehlende Funktionalität:** Bilderkennungs-Adapter (PlantNet API, Google Vision, PictureThis API); Onboarding-Schritt "Pflanze fotografieren" in REQ-020; Konfidenz-Schwelle für automatische vs. manuelle Bestätigung.

**Zielgruppe:** UZG-001 (Casual User), ZG-003 (Zimmerpflanzen-Enthusiasten als sekundäre Nutzung)

**Markttrend:** Wächst stark. PlantNet erreichte 2024 über 300 Millionen Bestimmungen pro Jahr. Nutzererwartung für "Pflanze fotografieren" ist in dieser Zielgruppe Standard.

---

### AG-002: Betriebswirtschaftliche Deckungsbeitragsrechnung

**Beschreibung:** Kalkulation der Produktionskosten pro Pflanze/Batch (Saatgut, Substrate, Dünger, Energie, Arbeitszeit) und Gegenrechnung mit erzielbarem Erlös. Deckungsbeitrag pro Kultur, ROI-Vergleich zwischen Anbaumethoden.

**Relevante bestehende REQs:** REQ-004 (Düngerverbrauch-Tracking), REQ-009 (Resource Dashboard: Cost per Gram, Energy Usage), REQ-014 (Tankbefüllungs-Historie), REQ-016 (InvenTree für Betriebsmittel-Kosten), REQ-013 (Batch als Kalkulationseinheit)

**Fehlende Funktionalität:** Saatgut-Einkaufspreise im Stammdaten-Modell, Stunden-Erfassung für Arbeitszeit, Energiekosten-Kalkulator, Erlös-Erfassung bei Ernte, Deckungsbeitragsauswertung per Kultur/Monat.

**Zielgruppe:** UZG-002 (Marktgärtner), ZG-005 (Cannabis Social Club), UZG-006 (Microgreens-Produzent)

**Markttrend:** Wächst mit dem gewerblichen Segment. Professionalisierung kleiner Betriebe erhöht den Bedarf an betriebswirtschaftlicher Steuerung.

---

### AG-003: Compliance-Dokumentation und Behörden-Reporting

**Beschreibung:** Strukturierte Auswertungen für Behörden-Kontrollen: CanG-konforme Ernte- und Abgabe-Dokumentation für Cannabis Social Clubs, PflSchG-konforme Behandlungsnachweise für gewerbliche Betriebe.

**Relevante bestehende REQs:** NFR-011 (CanG-Aufbewahrungsfristen), REQ-007 (Ernte-Dokumentation, Seed-to-Shelf-Traceability), REQ-010 (Behandlungsnachweise, Karenz-Intervalle), REQ-013 (Batch-IDs als Chargen-Nummern)

**Fehlende Funktionalität:** PDF-Report-Generator (Ernte-Protokoll, Behandlungsnachweis), behördenkonforme Datumsformate und Felder, digitale Signatur oder Export-Zertifizierung, Protokoll-Templates nach CanG/PflSchG.

**Zielgruppe:** ZG-005 (Cannabis Social Club), UZG-005 (Gewächshaus-Betrieb)

**Markttrend:** Wächst durch CanG-Liberalisierung in Deutschland (April 2024). Jede der inzwischen über 2.000 angemeldeten Anbauvereinigungen braucht Compliance-Tools.

---

### AG-004: Push-Notifikationen und Kanal-Management

**Beschreibung:** Zustellung von Pflegeerinnerungen, Sensorschwellwert-Alarmen und Task-Fälligkeiten über konfigurierbare Kanäle (E-Mail, Apprise, PWA-Push, Telegram, ntfy).

**Relevante bestehende REQs:** REQ-022 (generiert bereits Celery-Tasks für Erinnerungen), REQ-005 (Sensor-Alarme definiert), REQ-018 (Aktor-Ereignisse als Notification-Trigger), REQ-006 (Task-Fälligkeit)

**Fehlende Funktionalität:** Notification-Channel-Adapter (ABC-Interface in domain/interfaces/), Apprise-Integration für Pro-Nutzer, PWA-Service-Worker für Casual User, Kanal-Konfiguration in UserPreferences.

**Zielgruppe:** ZG-001 (Cannabis Grower, Sensor-Alarme), ZG-002 (Freilandgärtner, Frostwarnung), ZG-003 (Zimmerpflanzen, Gießerinnerungen), UZG-001 (Casual User, Pflege-Push)

**Markttrend:** Nutzererwartung für Push-Benachrichtigungen ist branchenübergreifend standard. Bereits als N-003 in MEMORY.md identifiziert.

---

### AG-005: Saatgut-Bank und Genetik-Archiv

**Beschreibung:** Verwaltung eigener Saatgutbestände (Restmengen, Keimfähigkeit, Erntejahr) und genetischer Archive (Mutterpflanzen-Stammbaum über mehrere Jahre). Besonders relevant für samenfeste Sorten und Züchtungsarbeit.

**Relevante bestehende REQs:** REQ-017 (Genetische Linie, Mutterpflanzen, descended_from-Graph), REQ-001 (seed_type: open_pollinated/f1_hybrid/landrace), REQ-016 (InvenTree für Saatgut-Inventar)

**Fehlende Funktionalität:** Saatgut-Collection mit Keimfähigkeits-Tracking (Keimrate, Lagerjahr), Richtlinien-Warnung bei abgelaufener Keimfähigkeit, Saatgut-Tausch zwischen Tenants, Sortenerhalt-Protokoll für Landrace-Sorten.

**Zielgruppe:** ZG-002 (Freilandgärtner, samenfeste Sorten), UZG-004 (Sammler, Rarität-Genetiken), UZG-007 (Forschung)

**Markttrend:** Saatgut-Souveränität wächst als Thema. Saatgut-Tausch-Netzwerke (Dreschflegel, Arche Noah) haben tausende aktive Mitglieder.

---

## 4. Persona-Gap-Analyse

| Persona-Bedürfnis | Status | Fehlende Funktionalität | Empfohlene REQ |
|-------------------|--------|------------------------|---------------|
| **Einfacher Einstieg (Onboarding ohne Vorwissen)** | Teilweise (REQ-020/021 vorhanden, aber kein Foto-Einstieg) | Foto-basierte Artbestimmung als Step 0 des Onboarding-Wizards | REQ-029 (KI-Bildidentifikation) |
| **Mobile Nutzung (unterwegs prüfen)** | Teilweise (React Web responsive, REQ-009 mobile-first erwähnt) | Native App fehlt (Flutter noch nicht implementiert), PWA ohne Service-Worker | REQ-030 (PWA + Push-Benachrichtigungen) |
| **Teamarbeit (Aufgaben delegieren)** | Gut (REQ-024, REQ-006 Aufgaben-Zuweisung) | RBAC Permission-Matrix noch nicht vollständig implementiert | REQ-024 v1.4 implementieren |
| **Kostenkontrolle (ROI berechnen)** | Minimal (REQ-009 nennt "Cost per Gram") | Keine Implementierung von Betriebskosten-Kalkulation, kein Deckungsbeitrag | REQ-031 (Betriebswirtschafts-Modul) |
| **Wissensaufbau (lernen und optimieren)** | Teilweise (REQ-021 Erfahrungsstufen, REQ-011 Stammdaten-Anreicherung) | Keine interaktiven Erklärungen, kein Lernpfad, kein Glossar in-app | In REQ-021 integrieren |
| **Compliance-Nachweis (Dokumentation)** | Minimal (Daten vorhanden, kein Reporting) | Kein PDF-Report-Generator, keine behördenkonformen Protokoll-Templates | REQ-032 (Compliance-Reporting) |
| **Skalierung (Betrieb vergrößern)** | Gut (Multi-Tenant, Kubernetes-Skalierung) | Keine Flächenbelegungsplanung, kein Staffelpreismodell für SaaS | REQ-002 Erweiterung |
| **Community (Austausch, Tipps)** | Minimal (REQ-024 Pinnwand nur innerhalb Tenant) | Kein öffentliches Forum, keine plattformübergreifende Companion-Planting-Community | Langfristig: Community-Feature |
| **Foto-Dokumentation (Wachstumslog)** | Minimal (REQ-007 erwähnt photo_refs als Felder) | Keine native Foto-Galerie pro Pflanze, kein visuelles Wachstums-Tagebuch | REQ-007/REQ-003 Erweiterung |
| **Offline-Nutzung (ohne Internet)** | Nicht adressiert | Kein Service-Worker-Cache, kein lokales Data-Sync | REQ-030 (PWA) |

---

## 5. Anwendungsgebiet x Zielgruppen-Matrix

|  | ZG-001 Cannabis | ZG-002 Freiland | ZG-003 Zimmer | ZG-004 GemGarten | ZG-005 Social Club | UZG-001 Casual | UZG-002 Marktgärtn. | UZG-003 Bildung | UZG-006 Microgreens |
|--|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Lifecycle Management** | OK | OK | OK | OK | OK | Teilweise | OK | Teilweise | OK |
| **Nährstoffmanagement** | OK | Teilweise | Teilweise | Teilweise | OK | Nein | Teilweise | Teilweise | OK |
| **Umgebungssteuerung** | OK | Teilweise | Nein | Nein | OK | Nein | Teilweise | Teilweise | OK |
| **Ernte-Dokumentation** | OK | OK | Nein | OK | OK | Nein | Teilweise | Teilweise | OK |
| **Mischkultur-Planung** | Nein | OK | Teilweise | OK | Nein | Nein | OK | Teilweise | Nein |
| **Compliance-Reporting** | Teilweise | Nein | Nein | Nein | Teilweise | Nein | Nein | Nein | Nein |
| **Kostenkontrolle/ROI** | Teilweise | Nein | Nein | Nein | Nein | Nein | Nein | Nein | Nein |
| **Teamarbeit/Kollaboration** | Teilweise | Teilweise | Nein | OK | OK | Nein | Teilweise | Teilweise | Nein |
| **Foto-Identifikation** | Nein | Nein | Nein | Nein | Nein | Nein | Nein | Teilweise | Nein |
| **Push-Benachrichtigungen** | Nein | Nein | Nein | Nein | Nein | Nein | Nein | Nein | Nein |
| **Aquaponik** | Nein | Nein | Nein | Nein | Nein | Nein | Nein | Teilweise | Nein |
| **Saatgut-Archiv** | Teilweise | Teilweise | Nein | Teilweise | Nein | Nein | Teilweise | Teilweise | Nein |

OK = vollständig adressiert | Teilweise = Basis vorhanden, Lücken | Nein = nicht adressiert

---

## 6. Empfehlungen

### Sofort umsetzbar (Quick Wins)

1. **KI-Bildidentifikation als Onboarding-Adapter (REQ-029):** Einen PlantNet- oder Google-Vision-Adapter im bestehenden REQ-011-Adapter-Pattern ergänzen. Im REQ-020-Onboarding-Wizard einen optionalen "Pflanze fotografieren"-Schritt vor Schritt 1 einfügen. Erwarteter Nutzen: Erschließt UZG-001 (Casual User) vollständig ohne Änderungen am Kernsystem. Aufwand: 2-3 Wochen. Bereits als wichtigstes zukünftiges Feature in MEMORY.md priorisiert.

2. **Push-Benachrichtigungen via Adapter (REQ-030-Vorstufe):** ABC-Interface `INotificationChannel` in `domain/interfaces/` + E-Mail-Adapter als erster produktiver Kanal. REQ-022-Celery-Tasks bereits vorhanden - nur die Zustellung fehlt. Zweite Phase: PWA-Service-Worker und optionaler Apprise-Adapter für Pro-Nutzer. Erwarteter Nutzen: Schließt die kritischste Lücke für ZG-003 (Zimmerpflanzen) und UZG-001 (Casual User). Aufwand: 1-2 Wochen für E-Mail, 2-3 Wochen für PWA.

3. **Foto-Dokumentation pro PlantInstance:** `photo_refs`-Felder sind in REQ-007 und REQ-010 bereits modelliert. Erweiterung um eine native Foto-Galerie mit Zeitstempel in der PlantInstance-Detailansicht. Erwarteter Nutzen: Senkt die Hemmschwelle für Casual User und Sammler, erhöht Bindung durch visuelles Wachstums-Tagebuch. Aufwand: 1 Woche.

### Mittelfristig (Nächste Entwicklungsphase)

1. **Betriebswirtschafts-Modul (REQ-031):** Erweiterung von REQ-013 (Batch als Kalkulationseinheit) um Kostenträger-Rechnung: Saatgut-Einkaufspreis, Substrat-Kosten, Dünger-Verbrauch (aus REQ-004/REQ-014 bereits geloggt), Energiekosten (kWh × Tarif), Arbeitszeit-Erfassung. Dashboard-Widget "Deckungsbeitrag pro Kultur/Monat". Benötigte neue REQs: REQ-031 Kostenträger-Rechnung. Adressiert UZG-002 (Marktgärtner), ZG-005 (Cannabis Social Club), UZG-006 (Microgreens-Produzent).

2. **Cannabis Social Club Compliance-Reporting (REQ-032):** PDF-Report-Generator für CanG-Protokolle auf Basis bestehender Daten (REQ-007 Ernte, REQ-010 Behandlungen, REQ-013 Batch-IDs, NFR-011 Aufbewahrungsfristen). Adressiert ZG-005 direkt. Marktpotenzial: 2.000+ angemeldete Anbauvereinigungen in Deutschland seit CanG April 2024. Aufwand: 3-4 Wochen.

3. **Saatgut-Bank-Modul (AG-005):** Neue `seed_stock`-Collection mit Erntejahr, Keimfähigkeits-Tracking und Restmenge. Integration mit REQ-001 (seed_type: open_pollinated) und REQ-016 (InvenTree-Inventar). Adressiert ZG-002, UZG-004 (Sammler). Aufwand: 2 Wochen.

4. **Bildungseinrichtungs-Starter-Kit:** Im REQ-020 Starter-Kit-System einen neuen Kit-Typ "Schulgarten/Labor" anlegen. Enthält vereinfachte Versuchsprotokolle, CSV-Export-Vorlage für Unterrichtsauswertung und einen Klassen-Tenant-Typ in REQ-024. Adressiert UZG-003. Aufwand: 1-2 Wochen.

### Langfristig / Strategisch

1. **Native Mobile App (Flutter, bereits in spec/stack.md geplant):** Flutter 3.16+ ist im Tech-Stack spezifiziert aber nicht implementiert. PWA als Zwischenschritt ist schneller und adressiert die dringlichsten mobilen Anforderungen. Strategisch wichtig für UZG-001 (Casual User erwartet App-Store-Eintrag) und ZG-003 (Zimmerpflanzen-Nutzung ist primär mobil). Empfehlung: PWA-Phase Q2 2026, Flutter-App Q4 2026.

2. **Vertical Farming / Container Farming als eigenständiges Anwendungsgebiet:** Die bestehende Architektur (Location-Hierarchie, DLI-Steuerung, Rezirkulations-Tanks) ist technisch bereit. Fehlt: Farming-spezifische Seed-Kits (NFT-Salat, DWC-Kräuter), Ertragsprognose-Modell, Staffelung nach Ebenen. Adressiert ZG-006 (Hydroponik-Betreiber), UZG-006 (Microgreens). Markttrend: Vertical Farming wächst weltweit 25% jährlich (Grand View Research 2024).

3. **Marktplatz und Community-Features:** Innerhalb des Multi-Tenant-Systems könnten Tenants optional Stammdaten, Nährstoffpläne und Starter-Kits in einem Community-Marktplatz teilen. Ähnlich wie REQ-001 Promotion-Workflow (tenant→system), aber mit Community-Rating. Adressiert das Netzwerk-Effekt-Problem: Je mehr Nutzer, desto besser die Daten. Strategische Empfehlung: Erst nach 10.000 aktiven Nutzern sinnvoll.

---

## 7. Prioritäts-Ranking: Neue Zielgruppen

| Rang | Zielgruppe | Gesamtscore | Empfehlung |
|------|-----------|-------------|-----------|
| 1 | UZG-001: Casual Hobby-Nutzer (Foto-Einstieg) | 20/25 | Sofort adressieren - KI-Bildidentifikation als Adapter |
| 2 | UZG-002: Marktgärtner / CSA-Betrieb | 18/25 | Mittelfristig - Betriebswirtschafts-Modul Q3 2026 |
| 3 | ZG-005: Cannabis Social Club (Compliance) | 17/25 | Mittelfristig - CanG-Reporting Q2 2026 |
| 4 | UZG-006: Microgreens-/Kräuter-Produzent | 19/25 | Mittelfristig - Sukzessionsplanung + Lieferterminkalkulation |
| 5 | UZG-003: Bildungseinrichtungen | 16/25 | Mittelfristig - Starter-Kit-Erweiterung ausreichend |
| 6 | UZG-004: Pflanzensammler (Orchideen/Kakteen) | 18/25 | Kurzfristig mit geringem Aufwand (Datenmodell-Erweiterung) |
| 7 | UZG-008: Aquaponik-Hobbyist | 18/25 | Mittelfristig - REQ-026 implementieren |
| 8 | UZG-005: Gewerblicher Gewächshaus-Betrieb | 15/25 | Langfristig - zu hoher Aufwand für aktuelle Phase |
| 9 | UZG-007: Forschungslabore | 15/25 | Langfristig - strategisch wertvoll, aber zu nischig |
| 10 | UZG-009: Permakultur-Praktiker | 13/25 | Perspektivisch - nach Marktreife |

---

## 8. Signalverzeichnis: Zielgruppen-Evidenz nach REQ

Dieses Verzeichnis dokumentiert die wichtigsten expliziten und impliziten Zielgruppen-Signale aus den Anforderungsdokumenten.

### Explizite Signale (direkt benannt)

| Signal | Fundstelle | Adressierte Gruppe |
|--------|-----------|-------------------|
| "Als Hobby-Gärtner, der zum ersten Mal Kamerplanter öffnet" | REQ-020 §1 Business Case | ZG-003, UZG-001 |
| "Als Zimmerpflanzen-Besitzer mit 15 Pflanzen" | REQ-022 §1 Business Case | ZG-003 |
| "Als Hobby-Aquaponiker mit einem Tilapia-Salat-DWC-System" | REQ-026 §1 Business Case | UZG-008 |
| "Als Betreiber einer Forellen-Kräuter-Aquaponikanlage" | REQ-026 §1 Business Case | UZG-008 |
| "Als Initiator eines Gemeinschaftsgartens" | REQ-024 §1 Business Case | ZG-004 |
| "Als ambitionierter Züchter" | REQ-001 §1 User Story Tenant-eigene Stammdaten | ZG-001 |
| "Als Plattform-Betreiber" | REQ-023, REQ-024 | Systemadministrator |
| "Cannabis Social Club" | REQ-001, REQ-024 | ZG-005 |
| "Als Datenschutzbeauftragter" | NFR-011 §1 User Story | ZG-005, UZG-005 |
| "Als Betreiber einer Anbauanlage" | NFR-011 §1 User Story | ZG-005 |
| "20 Tomaten ins Hochbeet setzen" | REQ-013 §1.1 Szenario | ZG-002 |
| "10 Stecklinge für den nächsten Erntezyklus" | REQ-013 §1.1 Szenario | ZG-001 |

### Implizite Signale (aus Funktionalität ableitbar)

| Signal | Fundstelle | Abgeleitete Gruppe | Begründung |
|--------|-----------|-------------------|------------|
| Trichom-Mikroskopie als Ernte-Indikator | REQ-007 §1 | ZG-001 (Cannabis) | Nur für Cannabis-Ernte relevant |
| Burping-Schedule für Jar-Curing | REQ-008 §2 | ZG-001 (Cannabis) | Spezifische Cannabis-Post-Harvest-Technik |
| Hermaphrodismus-Protokoll | REQ-010 §2 | ZG-001 (Cannabis) | Cannabis-spezifisches Problem |
| Phasenwechsel 18/6 → 12/12 | REQ-003, REQ-018 | ZG-001 (Photoperiodische Cannabis) | Typisches Cannabis-Lichtprogramm |
| Autoflower-Sonderlogik (60-90 Tage) | REQ-001, REQ-003 | ZG-001 (Cannabis Autoflower) | Exklusiv für Cannabis ruderalis-Hybriden |
| Hornspäne (50-80 g/m²), Jauchen (1:10) | REQ-004 §1 Organische Freiland-Düngung | ZG-002 (Freilandgärtner) | Typische organische Freiland-Praktiken |
| 4-Jahres-Fruchtfolge-Rotation | REQ-002 §1 | ZG-002 (Gemüsegärtner) | Klassische Gartenbau-Systematik |
| Winterhärte-Ampel (3 Stufen) | REQ-022 §1 User Story | ZG-002 (Freilandgärtner) | Nur für Außenbepflanzung relevant |
| Knollen-Zyklus Dahlie/Gladiole | REQ-022 §1 User Story | ZG-002 (Freilandgärtner) | Typische Gartenpraxis |
| Sukzessions-Aussaat (Salat-Staffel) | REQ-013 §1.1 Szenario 4 | ZG-002, UZG-006 | Planungs-Bedürfnis Marktgärtner |
| Care-Style-Preset "orchid" (Tauchbad) | REQ-022 §1 Tabelle | ZG-003 (Zimmerpflanzen) | Orchideen-spezifische Pflege |
| Kindel/Ableger-Vermehrung | REQ-017 §1 | ZG-003 (Zimmerpflanzen) | Typische Zimmerpflanzen-Vermehrung |
| Wasser-Bewurzelung (Pothos, Philodendron) | REQ-017 §1 | ZG-003, UZG-001 | Niedrigschwellige Methode |
| Light-Modus (kein Login) | REQ-027 §1 | UZG-001, ZG-003 Einzelnutzer | Barrier-Removal-Signal |
| 5-Gewächshaus-Betrieb (200 Pflanzen je) | NFR-002 §1.3 | UZG-005 (Gewächshaus-Betrieb) | Implizite Betriebsgröße im Skalierungs-Szenario |
| CanG-Aufbewahrungsfristen | NFR-011 §1.2 | ZG-005 (Social Club) | Gesetzliche Compliance-Pflicht |
| InvenTree-Integration | REQ-016 | ZG-006 (Semi-Pro Hydro), UZG-005 | Professionelle Betriebsmittel-Verwaltung |
| Kubernetes-Skalierung (HPA) | NFR-002 | Enterprise-/Plattform-Segment | Professionelles Deployment-Szenario |

---

*Analysebasis: Alle Anforderungsdokumente in spec/req/ und spec/nfr/ im Stand 2026-03-21. Marktdaten basieren auf öffentlich verfügbaren Quellen (Grand View Research, App-Store-Statistiken, Vereinsregistrierungen CanG). Für strategische Entscheidungen empfiehlt sich eine primäre Marktforschung durch direkte Nutzerbefragungen.*
