# Zielgruppen-Spezifikationen

Detaillierte Zielgruppen-Dokumente fuer kontextbezogene Evaluierung, Testfall-Ableitung und Persona-basierte Anforderungspruefung.

**Quelle:** Abgeleitet aus `spec/analysis/target-audience-analysis.md`

---

## Primaere Zielgruppen (stark adressiert)

| ID | Datei | Zielgruppe | Tech-Affinitaet |
|----|-------|-----------|-----------------|
| ZG-001 | [Cannabis Indoor Grower](ZG-001_Cannabis-Indoor-Grower.md) | Heimanbau bis Semi-Professionell, 4-50 Pflanzen | Hoch |
| ZG-002 | [Freilandgaertner](ZG-002_Freilandgaertner.md) | Hobby-Gemuese-/Kraeutergarten, 20-200 Pflanzen | Gering-Mittel |
| ZG-003 | [Zimmerpflanzen-Enthusiast](ZG-003_Zimmerpflanzen-Enthusiast.md) | Casual bis Sammler, 5-80 Pflanzen | Gering-Mittel |

## Sekundaere Zielgruppen (teilweise adressiert)

| ID | Datei | Zielgruppe | Tech-Affinitaet |
|----|-------|-----------|-----------------|
| ZG-004 | [Gemeinschaftsgarten](ZG-004_Gemeinschaftsgarten.md) | Mitglied oder Admin, 5-50 Mitglieder | Gering-Mittel |
| ZG-005 | [Cannabis Social Club](ZG-005_Cannabis-Social-Club.md) | CanG-konformer Anbauverein, 10-500 Mitglieder | Mittel-Hoch |
| ZG-006 | [Hydroponik-Betreiber](ZG-006_Hydroponik-Betreiber.md) | Semi-prof. NFT/DWC/Vertical Farming | Hoch |

## Unterversorgte Zielgruppen (nicht/minimal adressiert)

| ID | Datei | Zielgruppe | Potenzial |
|----|-------|-----------|-----------|
| UZG-001 | [Casual Hobby-Nutzer](UZG-001_Casual-Hobby-Nutzer.md) | Kein botanisches Vorwissen, Foto-Einstieg | Sehr Hoch |
| UZG-002 | [Marktgaertner / CSA](UZG-002_Marktgaertner.md) | Kleinbetrieb mit Direktvermarktung | Hoch |
| UZG-003 | [Bildungseinrichtungen](UZG-003_Bildungseinrichtungen.md) | Schule, Berufsschule, Uni-Labor | Mittel (Multiplikator) |
| UZG-004 | [Pflanzensammler](UZG-004_Pflanzensammler.md) | Orchideen/Kakteen/Bromelien-Spezialisten | Mittel |
| UZG-005 | [Gewaechshaus-Betrieb](UZG-005_Gewaechshaus-Betrieb.md) | Gewerbliche Zierpflanzen-Produktion | Gross (schwer zugaenglich) |
| UZG-006 | [Microgreens-Produzent](UZG-006_Microgreens-Produzent.md) | Gastronomie-Belieferung | Wachsend |

---

## Dokumentstruktur

Jedes Zielgruppen-Dokument folgt einer einheitlichen Struktur:

1. **Profil** -- Tabellarische Uebersicht (Bezeichnung, Alter, Betriebsgroesse, Tech-Affinitaet)
2. **Persona** -- Konkrete Person mit Name, Situation und Motivation
3. **Kernbeduerfnisse** -- Detaillierte funktionale Anforderungen mit REQ-Verweisen
4. **Typische Workflows** -- Schritt-fuer-Schritt Nutzungsszenarien
5. **Relevante REQs** -- Tabelle mit Relevanz-Bewertung pro REQ
6. **Abgrenzung** -- Vergleich zu aehnlichen Zielgruppen
7. **Evaluationskriterien** -- 10 Prueffragen fuer kontextbezogene Evaluierung
8. **Sprachstil und Fachbegriffe** -- Zielgruppen-spezifisches Vokabular

## Verwendungszweck

- **Eval-Dokumente:** Evaluationskriterien (Abschnitt 7) als Grundlage fuer RAG-Eval und E2E-Testfaelle
- **Persona-Tests:** Typische Workflows (Abschnitt 4) als Basis fuer User-Journey-Tests
- **Sprachliche Anpassung:** Fachbegriffe (Abschnitt 8) fuer zielgruppen-gerechte UI-Texte und Hilfe
- **Anforderungs-Reviews:** Kernbeduerfnisse (Abschnitt 3) fuer Vollstaendigkeitspruefung
- **Priorisierung:** Abdeckungsgrad und Potenzial fuer Product-Backlog-Priorisierung
