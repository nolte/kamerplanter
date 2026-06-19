# Lizenz- & Nutzungsanalyse: awesome-agriculture-Integrationen (REQ-037 – REQ-041)

```yaml
Dokument: Lizenz- und Nutzungsanalyse
Bezug: REQ-037, REQ-038, REQ-039, REQ-040, REQ-041
Maßstab: Kamerplanter ist MIT-lizenziert, wird als Quelltext öffentlich auf GitHub
         verteilt und self-hosted via Kubernetes/Helm betrieben.
Status: Analyse (Entwurf)
Datum: 2026-06-20
Methodik: Jede Lizenz/jeder Nutzungsstatus wurde an der Originalquelle verifiziert
          (LICENSE-Datei, PyPI-Metadaten, Datennutzungs-Policy, Live-API-Probe).
```

## 1. Zweck & Maßstab

Diese Analyse prüft jedes in REQ-037 bis REQ-041 referenzierte Drittprojekt auf
zwei Fragen:

1. **Lizenztechnische Nutzbarkeit** gegen die **MIT**-Lizenz von Kamerplanter
   (permissiv, Outbound öffentlich verteilt). Maßgeblich ist nicht nur „Open Source",
   sondern die konkrete Copyleft-/Auflagen-Wirkung auf **Code** *und* **Daten**.
2. **Direktnutzung vs. Idee-Vorlage** — soll das Projekt als Dependency/Datenquelle
   eingebunden werden, oder dient es nur als konzeptionelle Vorlage (weil tot,
   sprachfremd, geografisch unpassend oder lizenzrechtlich heikel)?

### Lizenz-Grundregeln (Kurzreferenz)

| Lizenztyp | Wirkung auf MIT-Code | Wirkung auf übernommene Daten |
|-----------|----------------------|-------------------------------|
| **MIT / BSD-2 / BSD-3 / ISC / Apache-2.0** | ✅ voll kompatibel, nur Copyright-Notice erhalten | — |
| **MPL-2.0** | ✅ kompatibel — **datei-basiertes** Copyleft, infiziert das Gesamtwerk **nicht**, solange MPL-Dateien unverändert/separat bleiben | — |
| **(L)GPL-3.0 / AGPL-3.0** | ❌ **starkes Copyleft** — Import/Linking zwingt das verteilte Gesamtwerk unter (A)GPL → unvereinbar mit MIT-Outbound | — |
| **CC0 / Public Domain** | — | ✅ frei, keine Auflagen |
| **CC-BY 4.0** | — | ✅ nutzbar, **Attribution** Pflicht (UI + Export) |
| **CC-BY-SA 3.0/4.0** | berührt MIT-Code **nicht** | ⚠️ **ShareAlike** — verschmolzene Daten-Sammlung muss CC-BY-SA bleiben + Attribution |
| **Proprietäre Custom-Terms** | ❌ nicht als MIT redistribuierbar | nur unter Originalauflagen (z. B. Logo-/Disclaimer-Pflicht) |

> **Faustregel:** Code-Copyleft (GPL/AGPL) ist die Gefahr für unsere **Software-Lizenz**.
> Daten-Copyleft (CC-BY-SA) ist die Gefahr für unsere **exportierbare Wissensbasis** (REQ-032),
> nicht für den Code.

## 2. Gesamtmatrix

| REQ | Projekt | Artefakt | Lizenz (verifiziert) | MIT-verträglich? | Empfehlung |
|-----|---------|----------|----------------------|------------------|------------|
| 037 | **aquacrop-eto** (`aquacropeto`) | Python-Lib (PyPI) | BSD-3-Clause | ✅ Ja | 🟢 **Direkt nutzen** (Dependency) |
| 037 | PyETo (Upstream) | Python-Quellcode | BSD-3-Clause | ✅ Ja | 🟡 Idee / vendored (kein PyPI, pre-alpha) |
| 037 | `evapotranspiration` (PyPI) | Python-Lib | MIT | ✅ Ja | 🟡 Idee / Fallback (2020, Beta) |
| 037 | **pyTSEB** | Python-Lib | **GPL-3.0-or-later** | ❌ **Nein** | 🔴 **Meiden** als Dependency (nur Konzept / separater Prozess) |
| 038 | **PlantCV** | Python-Lib (PyPI) | MPL-2.0 | ✅ Ja (bedingt) | 🟢 **Direkt nutzen** (nicht in PlantCV-Dateien patchen) |
| 038 | **PlantDoc** | Dataset | CC-BY-4.0 | ✅ Ja | 🟢 **Training nutzen** (Attribution) |
| 038 | **PlantVillage** | Dataset | **mehrdeutig** (CC-BY-SA 3.0 ↔ CC0, Repo ohne LICENSE) | ⚠️ ungeklärt | 🟠 **Entscheidung nötig** — Lizenz fixieren oder fallenlassen |
| 039 | frostline (Parser) | Code | MIT | ✅ Ja | 🟡 **Idee-Vorlage** (Static-API-Schema) |
| 039 | USDA/PHZM-Daten (PRISM/OSU) | Dataset | **proprietäre PRISM/OSU-Terms** (US-only) | ❌ Nein | 🔴 Nicht einchecken (nur opt. US-Adapter mit Logo-Auflage) |
| 039 | **DWD Open Data** | Dataset | GeoNutzV (Quellenpflicht) | ✅ Ja | 🟢 **DACH-Datenbasis** für eigene Zonenableitung |
| 039 | **Open-Meteo** | API/Daten | CC-BY-4.0 (Daten) | ✅ Ja | 🟢 **DACH-Datenbasis** (Attribution) |
| 040 | OpenFarm | Rails-App + Daten | Code MIT / **Daten CC0** | ✅ (Daten frei) | 🟠 Server **tot** (4/2025) → nur statischer CC0-Dump, kein Live-Adapter |
| 040 | **Growstuff** | Rails-App + Daten | Code AGPL-3.0 / **Daten CC-BY-SA 3.0** | ⚠️ Daten-ShareAlike | 🟠 **Entscheidung nötig** — isolieren oder nur Mapping-Idee |
| 041 | **NASA POWER** | API + Daten | CC-BY-4.0, keyless | ✅ Ja | 🟢 **Direkt nutzen** (eigener Py-Adapter, Attribution + Cache) |
| 041 | agroclimatology | Ruby-Lib | MIT | ❌ (Ruby, tot seit 2016) | 🟡 Idee-Vorlage (grob) |

**Legende:** 🟢 direkt nutzen · 🟡 Idee/Vorlage · 🟠 Entscheidung/Auflagen nötig · 🔴 meiden

## 3. Detailbefunde je Projekt

### REQ-037 — Evapotranspiration

- **aquacrop-eto** (`pip install aquacropeto`, BSD-3-Clause) — der de-facto installierbare
  PyETo-Nachfolger (FAO-56 Penman-Monteith). **Direkt nutzbar.** Einschränkung: letztes
  Release 2022 → vor Produktiveinsatz Python-3.14-Kompatibilität prüfen, sonst vendored
  einbinden (Copyright-Notice „Mark Richards" erhalten).
- **PyETo** (BSD-3) — lizenzrechtlich unbedenklich, aber pre-alpha, kein PyPI-Artefakt.
  Nur als Quellcode-Vorlage relevant; der Fork ist die bessere Wahl.
- **`evapotranspiration`** (MIT, 2020 Beta) — lizenzideal, aber ungepflegt; nur Fallback.
- **pyTSEB** (GPL-3.0-or-later, aktiv) — **lizenzrechtlich tabu als Import.** GPL-3.0 ist
  starkes Copyleft: ein Import zwänge das öffentlich verteilte Gesamtwerk unter GPL und
  bräche das MIT-Outbound-Versprechen. Falls die Two-Source-Energy-Balance-Methodik je
  gebraucht wird: Algorithmus eigenständig nachbauen **oder** strikt als separater
  Prozess/Microservice auslagern (selbst das ist bei GPL juristisch heikel).

### REQ-038 — CV-Pflanzendiagnose

- **PlantCV** (MPL-2.0, aktiv, v4.11/2026) — **direkt nutzbar** als unveränderte Library
  oder separater Service (passt zum `knowledge-service`-Pattern). MPL-2.0-Copyleft ist
  **datei-granular**: Solange keine PlantCV-Quelldatei direkt modifiziert wird, bleibt der
  MIT-Code unberührt. **Regel:** wrappen/erweitern in eigenen Dateien, nicht hineinpatchen.
  Notice (Lizenzhinweis + Link) mitliefern. Hinweis: PlantCV ist Phänotypisierung/
  Vorverarbeitung, **kein** fertiges Krankheits-Diagnosemodell.
- **PlantDoc** (CC-BY-4.0) — **sauberste Trainingsquelle**: kommerzielle Nutzung + Modell-
  Weitergabe ohne ShareAlike erlaubt, nur Attribution. Reale „in the wild"-Bilder (gut gegen
  das Lab→Feld-Gap), aber klein (~2.600 Bilder) → Fine-Tuning-Schicht, nicht alleinige Basis.
  Nebenrisiko: gescrapte Originalbilder (lizenzunabhängiges Web-Scraping-Restrisiko).
- **PlantVillage** — **kritischstes Lizenz-Finding.** Das Original-Repo `spMohanty/
  PlantVillage-Dataset` enthält **kein LICENSE-File**; maßgebliche Quellen widersprechen sich:
  PSU/Zenodo nennen **CC-BY-SA 3.0** (ShareAlike!), einzelne Kaggle-Mirror **CC0**. Keine
  NonCommercial-Klausel in beiden Lesarten — aber die ShareAlike-Lesart würde abgeleitete
  Daten (Modellgewichte als „Derivat" ist juristisch umstritten) binden. **Vor Produktiv-
  nutzung Lizenzquelle verbindlich fixieren** (z. B. nur eine explizit CC0-deklarierte,
  dokumentierte Spiegelung verwenden — oder den Datensatz fallenlassen). Da Labordaten
  ohnehin nur als Vortrainings-Ergänzung taugen, ist der Verzicht eine reale Option.

### REQ-039 — Klimazonen / Winterhärte

- **frostline-Code** (MIT) — frei verwendbar; wertvoll als **Architektur-Vorlage**
  („Static-JSON-pro-Geo-Schlüssel"-Muster).
- **USDA/PHZM-Daten** (PRISM Climate Group / Oregon State University) — **proprietäre Custom-
  Terms**, nicht gemeinfrei: redistribuierbar nur mit USDA-ARS- **und** OSU-Logo bzw. (bei
  Veränderung) Disclaimer + Logo-Entfernung; Eigentum bleibt OSU. **US-only** (ZIP-basiert) →
  für DACH fachlich wertlos. **Nicht** in ein MIT-Repo einchecken; höchstens optionaler
  US-Laufzeit-Adapter gegen `phzmapi.org` unter Erfüllung der Auflagen.
- **DACH-Weg (empfohlen):** Eigene Zonenableitung aus **DWD Open Data** (GeoNutzV, kostenfrei
  auch kommerziell, Pflicht „Datenbasis: Deutscher Wetterdienst") und/oder **Open-Meteo**
  (Daten CC-BY-4.0, Attribution „Weather data by Open-Meteo.com"). Beide MIT-verträglich.
  **Eine fertige, lizenzklare freie DACH-Winterhärtezonen-Karte existiert nicht** — sie muss
  selbst aus Klimanormalen abgeleitet werden (deckt sich mit dem REQ-039-Plan).

### REQ-040 — Wissensbasis-Enrichment

- **OpenFarm** — Code MIT, **Daten CC0** (ideal, keine Auflagen). **Aber:** Repo seit
  **April 2025 archiviert**, Server abgeschaltet, API antwortet nur noch mit 301-Redirect.
  Ein **Live-Adapter ist nicht realisierbar.** Nutzbar nur als **einmaliger statischer CC0-
  Dump-Import** aus einem Mirror — nicht als wartbare REQ-040-Live-Quelle.
- **Growstuff** — Code AGPL-3.0 (**irrelevant**, da nur Daten via API konsumiert werden),
  **Daten CC-BY-SA 3.0 Unported** (nur strukturierte Fakten; Member-Fotos/-Kommentare sind
  separat geschützt). API ist **live** (verifiziert: `GET /crops.json` → HTTP 200). Der
  **ShareAlike-Knackpunkt:** Verschmilzt man Growstuff-Felder mit eigenen Species-Daten
  („Adaptation"), muss die **abgeleitete Daten-Sammlung** unter CC-BY-SA stehen + Growstuff
  attribuiert werden — das bindet **jeden Export/Druck** (Kollision mit REQ-032). Vermeidbar
  nur durch **strikte Isolation** (Growstuff-Daten in eigener Collection, kein Merge in
  Stammfelder → „Collection"-Ausnahme) **oder** indem das Feld-Mapping bloß als **Vorlage**
  dient und keine Werte importiert werden.

### REQ-041 — Agroklimatologie

- **NASA POWER** (CC-BY-4.0, keyless, aktiv) — **direkt nutzbar.** Eigener Python-Adapter
  gegen die freie REST-API; Daten dürfen gespeichert, angezeigt, exportiert werden.
  Pflichten: **Attribution** (POWER-Acknowledgement-Text in UI/Export), **Fair-Use/Throttle**
  (kein hartes Limit dokumentiert, aber HTTP 429 bei Überlast → clientseitiges Caching,
  keine Mehrfach-Requests auf dieselbe 0.5°-Gitterzelle).
- **agroclimatology** (Ruby, MIT, letztes Release 2016, veralteter Endpoint) — nur grobe
  **Ideen-Vorlage**; nicht portieren, der Adapter wird direkt gegen die aktuelle POWER-REST-API
  gebaut.

## 4. Auswirkungen auf die REQ-Dokumente

Die Verifikation korrigiert mehrere Annahmen in den am 2026-06-19 erstellten REQ-Entwürfen:

| REQ | Korrektur-/Schärfungsbedarf |
|-----|------------------------------|
| 037 | pyTSEB klar als **🔴 GPL-3.0 = meiden** kennzeichnen (nicht nur „GPL-Schwergewicht/Zukunfts-Option"); `aquacropeto` (nicht `aquacrop-eto`) als korrekter PyPI-Name. |
| 038 | PlantVillage-Lizenz als **ungeklärt/Risiko** markieren (Repo ohne LICENSE); **PlantDoc (CC-BY-4.0) als primäre, saubere Trainingsquelle** aufnehmen; PlantCV-„nicht-modifizieren"-Regel ergänzen. |
| 039 | frostline-**Daten** als proprietär/US-only klarstellen; **DWD (GeoNutzV) + Open-Meteo (CC-BY-4.0)** als kanonische DACH-Datenbasis verankern. |
| 040 | OpenFarm-**Live-Adapter streichen** → nur statischer CC0-Dump; Growstuff-**ShareAlike-Export-Konflikt mit REQ-032** als load-bearing Caveat schärfen (Isolation vs. Idee). |
| 041 | Bereits korrekt (NASA POWER direkt, agroclimatology nur Idee) — keine Korrektur nötig. |

Außerdem (aus vorheriger Erstellung): **REQ-011 §1.1** führt OpenFarm fälschlich als
CC-BY-4.0 — verifiziert ist **CC0**.

## 5. Entscheidungen (getroffen 2026-06-20)

1. **PlantVillage:** ✅ **Fallengelassen** — Lizenz ungeklärt (Repo ohne LICENSE, CC-BY-SA↔CC0
   widersprüchlich). Es werden nur **PlantDoc (CC-BY-4.0)** + eigene Realdaten genutzt.
2. **Growstuff:** ✅ **Nur Mapping-Idee** — keine Wertübernahme, damit die exportierbare
   Wissensbasis CC-BY-SA-frei bleibt (kein Konflikt mit REQ-032).
3. **OpenFarm:** ✅ **Optionaler einmaliger CC0-Dump** (kein Live-Adapter, da Server seit
   04/2025 abgeschaltet).
4. **REQ-038 (CV-Diagnose):** ✅ **Nach Welle 1** terminiert (eigenständige ML-Initiative).

Eingearbeitet in REQ-038 v1.1, REQ-040 v1.1 und den Integrationsplan
(`.audits/awesome-agriculture-integration-plan.md` §5).

## 6. Fazit

- **Sofort und sauber direkt nutzbar:** `aquacropeto` (BSD-3), PlantCV (MPL-2.0),
  PlantDoc (CC-BY-4.0), NASA POWER (CC-BY-4.0), DWD Open Data, Open-Meteo.
- **Nur als Idee/Vorlage:** PyETo-Upstream, frostline (Schema), agroclimatology (Ruby).
- **Klar meiden (Lizenzkonflikt):** pyTSEB (GPL-3.0) als Dependency; USDA/PHZM-Daten als
  eingecheckter Datenbestand.
- **Entscheidung erforderlich:** PlantVillage (Lizenz ungeklärt), Growstuff (Daten-ShareAlike),
  OpenFarm (Server tot, nur Dump).

Die fünf Integrationsideen bleiben fachlich tragfähig; die lizenzrechtlich sicherste
Gesamtkonfiguration stützt sich auf permissive Libraries (BSD/MIT/MPL), CC0/CC-BY-Daten
(PlantDoc, NASA POWER, OpenFarm-Dump, DWD/Open-Meteo) und behandelt CC-BY-SA (Growstuff) sowie
ungeklärte Lizenzen (PlantVillage) als bewusst einzugrenzende Sonderfälle.
