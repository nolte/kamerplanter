# N-001 — Foto-basierte Pflanzenerkennung: Deep-Research Bericht

> **Quelle:** N-001 aus `spec/analysis/casual-houseplant-user-review.md` (Foto-basierte Pflanzenerkennung fehlt — Dealbreaker für Casual-User).
> **Branch:** `feat/plant-image-recognition` · **Erstellt:** 2026-06-15 · **Methode:** Multi-Source Deep-Research mit adversarialer Faktenprüfung (6 Such-Winkel, 27 Quellen gefetcht, 124 Claims extrahiert, 25 adversarial verifiziert → 20 bestätigt / 5 widerlegt).
> **Auftrag:** Lizenz- und kostenneutrale Umsetzungsoptionen für Pflanzenerfassung per Bilderkennung — drei Aufgaben: (A) Artbestimmung, (B) Krankheits-/Schädlingserkennung, (C) Zustand/Phänologie.

---

## 1. Executive Summary

Für N-001 ist ein **hybrider, self-hosting-first Ansatz** die **einzige** Strategie, die beide harten Nebenbedingungen erfüllt (permissive Lizenz **und** keine Endnutzerkosten):

- **Aufgabe A — Artbestimmung (Kern):** Ein **DINOv2-ViT-Backbone** ist der Industriestandard (PlantCLEF 2024 nutzt genau diese Architektur). Das **Meta-Basismodell und die ONNX-Tooling sind Apache-2.0** und voll ONNX-exportierbar — passend zum vorhandenen ONNX-Embedding-Service. Die fertig auf 7.806 Arten fine-getunten PlantCLEF-Gewichte sind jedoch **CC-BY-NC (nicht-kommerziell)** und damit für ein potenziell kommerzielles Produkt disqualifiziert. Sauberer Weg: **Embedding-basiertes Ähnlichkeits-Matching** mit dem Apache-2.0-Backbone gegen die eigenen 210 Steckbriefe (mit selbst beschafften, lizenzkonformen Referenzbildern) + ArangoDB-Vektorsuche.
- **Aufgabe B — Krankheits-/Schädlingserkennung (REQ-010 IPM):** **PlantDoc** ist der geeignete, real-world-orientierte Datensatz. Fine-Tuning auf PlantDoc senkt den Klassifikationsfehler um **bis zu 31 %** gegenüber Labordaten (PlantVillage überträgt **nicht** auf Feldfotos).
- **Aufgabe C — Zustand/Phänologie:** **Kein fertiges, frei lizenziertes Modell gefunden.** Hier ist Eigentraining eines Klassifikatorkopfs auf DINOv2-Embeddings mit projekteigenen Bildern entlang der REQ-003-Phasen nötig. *(Evidenzschwach — Abwesenheit von Belegen, sollte gezielt nachrecherchiert werden.)*
- **Externe APIs:** Alle kommerziellen Foto-APIs (Pl@ntNet kommerziell, plant.id/Kindwise) sind **pro Request kostenpflichtig** und fallen unter Constraint #2 raus. **Pl@ntNet** bleibt nur als optionaler, datenschutzfreundlicher **Free-Tier-Fallback** (≤500 Anfragen/Tag, Fotos werden nicht persistiert) nutzbar.

---

## 2. Lizenz- & Kosten-Risikomatrix

| Lösung | Aufgabe | Lizenz | Self-host? | Endnutzerkosten | Verdikt |
|---|---|---|---|---|---|
| **DINOv2 Basis-Backbone (Meta)** | A, B, C | **Apache-2.0** ✅ | ✅ (ONNX) | keine | **Empfohlen** — Embedding-Extraktor |
| PlantCLEF-2024 Fine-tune-Gewichte (7.806 Arten) | A | **CC-BY-NC** ⚠️ | ✅ | keine | **Disqualifiziert** (nicht-kommerziell)¹ |
| iNaturalist Modelle (~500 Taxa) | A | **MIT** ✅ | ✅ | keine | Nutzbar, aber zu wenig Arten-Abdeckung |
| iNaturalist Vollmodelle | A | — | ❌ (privat) | — | Nicht verfügbar |
| **PlantDoc-Datensatz** | B | CC (real-world) ✅ | ✅ | keine | **Empfohlen** für IPM-Fine-Tuning |
| PlantVillage-Datensatz | B | offen | ✅ | keine | Nur ergänzend (Laborbilder, schlechter Transfer) |
| PlantNet-300K-Datensatz | A | s. Repo-LICENSE | ✅ | keine | Für Training prüfen |
| **Pl@ntNet API (Free-Tier)** | A | ToS, ≤500/Tag | ❌ (extern) | keine bis 500/Tag | **Fallback** (DSGVO-vertretbar)² |
| Pl@ntNet API (kommerziell) | A | kostenpflichtig | ❌ | **≥1.000 €/Jahr** | Disqualifiziert (Constraint #2) |
| plant.id / Kindwise | A, B | pro Request | ❌ | **0,05 €/Credit, min. 50 €** | Disqualifiziert (Constraint #2) |
| Pl@ntNet **Bilder** als Trainingsdaten | A | **CC-BY-SA** ⚠️ | — | — | ShareAlike-Risiko für proprietäre Nutzung |
| iNaturalist **Content** als Trainingsdaten | A | **CC-BY-NC** (default) ⚠️ | — | — | Nur CC0/CC-BY-Teilmengen kommerziell nutzbar³ |

¹ Der CC-BY-NC-Lizenz-Claim wurde im Voting formal 1-2 abgelehnt, aber vom Verifier als nachgelagerte Einschränkung dokumentiert — **vor jeder Verwendung der fertigen Klassifikatorgewichte rechtlich abklären**. Die Embedding-only-Variante umgeht das Problem komplett.
² Fotos werden nicht in der DB gespeichert (nur flüchtig im RAM während der Erkennung), aber Query-Metadaten (Datum/Zeit/Bild-URL) werden ohne genannte Retention-Frist gespeichert.
³ Das in der Vorrecherche kursierende **pauschale iNaturalist-Verbot von KI-Training wurde widerlegt (0-3)** — der einschränkende Faktor ist die CC-BY-NC-Default-Lizenz, kein Pauschalverbot.

---

## 3. Befunde im Detail

### Aufgabe A — Artbestimmung

**A1 · DINOv2-ViT ist die etablierte Architektur** · Konfidenz: **hoch** (3-0)
Das PlantCLEF-2024-Modell ist ein DINOv2-Fine-tune (`vit_base_patch14_reg4_dinov2_lvd142m_pc24`) auf ~1,4 Mio Bildern / 7.806 Gefäßpflanzenarten; die Referenzsysteme des Wettbewerbs sind ViT-Backbones. Das Basis-DINOv2 von Meta und die ONNX-Tooling sind **Apache-2.0** und voll ONNX-exportierbar — ideal für Embedding-Extraktion im vorhandenen Kamerplanter-ONNX-Stack.
- https://huggingface.co/vincent-espitalier/dino-v2-reg4-with-plantclef2024-weights
- https://arxiv.org/pdf/2509.15768 · https://arxiv.org/html/2407.06298v1
- https://github.com/sefaburakokcu/dinov2_onnx · https://github.com/facebookresearch/dinov2

**A2 · PlantCLEF-Gewichte sind CC-BY-NC + Scope-Mismatch** · Konfidenz: **mittel**
CC-BY-NC (nicht-kommerziell) → nicht direkt für ein kommerzielles Produkt verwendbar. Zudem ist der Datensatz auf die **Wildflora Südwesteuropas** zugeschnitten — tropische Zimmerpflanzen, Cannabis und Kultur-Kultivare (Kamerplanters Zielarten) sind unterrepräsentiert. **Empfehlung:** nicht die Klassifikatorgewichte ausliefern, sondern das Apache-2.0-Basis-DINOv2 als Embedding-Extraktor nutzen.
- https://zenodo.org/records/10848263

**A3 · Architektur: Embedding-Matching ist der saubere Kernweg** · Konfidenz: **hoch** (abgeleitet aus 3-0-Claims)
DINOv2-Embeddings (ViT-B/14 distilled) wurden nachweislich für Pflanzenklassifikation im 7.800-Arten-Maßstab eingesetzt. Few-Shot/Embedding-Matching vermeidet das CC-BY-NC-Klassifikator-Problem komplett und passt zum vorhandenen Knowledge-Service-Microservice-Muster (ONNX Runtime, Adapter-Registry) + ArangoDB-Vektorsuche.
- https://docs.arangodb.com/3.13/aql/functions/vector/ · https://github.com/plantnet/PlantNet-300K

**A4 · iNaturalist nur eingeschränkt self-hostbar** · Konfidenz: **hoch** (3-0 / 2-1)
Veröffentlicht werden nur kleine Modelle (~500 Taxa) + Geo-/Taxonomie-Dateien unter **MIT-Lizenz** (verkaufen/sublizenzieren erlaubt); die vollständigen Artklassifikatoren bleiben aus IP-Gründen privat. Die ~500-Taxa-Modelle decken Kamerplanters Zielarten nicht ausreichend ab.
- https://github.com/inaturalist/model-files

### Aufgabe B — Krankheits-/Schädlingserkennung (REQ-010 IPM)

**B1 · PlantDoc ist der geeignete Datensatz** · Konfidenz: **hoch** (3-0)
2.598 Bilder, 13 Pflanzenarten, 27 Klassen (17 Krankheiten + 10 gesund), aus realen Internet-Bildern annotiert. Fine-Tuning auf PlantDoc statt auf Labordaten senkt den Klassifikationsfehler um **bis zu 31 %** — Labordatensätze (PlantVillage) übertragen **nicht** auf Feldfotos. Caveat: Arten v.a. Gemüse/Obst (Tomate, Kartoffel, Mais, Paprika), wenig Kräuter; Detection-Leistung moderat (mAP ~38,9).
- https://arxiv.org/pdf/1911.10317 · https://github.com/pratikkayal/PlantDoc-Dataset

### Aufgabe C — Zustand/Phänologie

**C1 · Kein fertiges Modell gefunden** · Konfidenz: **niedrig** (Abwesenheit von Evidenz)
Keiner der 20 verifizierten Claims betrifft Phänologie-/Stadienmodelle. Pragmatisch: phänologische Klassifikation ist eng an Kamerplanters Phasen-Statemachine (REQ-003) gekoppelt → als überwachte Klassifikation auf eigenen Bildern umsetzen (DINOv2-Embeddings + leichter Klassifikatorkopf). **Dieser Befund ist evidenzschwach und sollte gezielt nachrecherchiert werden.**

### Externe APIs & Fallback

**E1 · Pl@ntNet Free-Tier als DSGVO-vertretbarer Fallback** · Konfidenz: **hoch** (3-0)
Dauerhaft kostenlos bis **500 Identifikationen/Tag**; Nutzerfotos werden **nicht** in der DB gespeichert (nur flüchtig im RAM). Kommerzielle Nutzung darüber kostenpflichtig (ab 1.000 €/Jahr / 200.000 Requests). Query-History (Datum/Zeit/Bild-URL) wird ohne genannte Retention-Frist gespeichert.
- https://my.plantnet.org/terms_of_use · https://my.plantnet.org/pricing

**E2 · Pl@ntNet-Daten/Bilder mit Lizenzpflichten** · Konfidenz: **hoch** (3-0)
Beobachtungsdaten **CC-BY**, Bilder **CC-BY-SA** (ShareAlike — Derivate müssen unter gleicher Lizenz geteilt werden) + Pl@ntNet-Nennung. ShareAlike kann abgeleitete Modellgewichte/Datensätze betreffen → für proprietäre kommerzielle Nutzung problematisch.
- https://docs.plantnet.org/en/reference/data-and-image-licensing/

**E3 · plant.id / Kindwise disqualifiziert** · Konfidenz: **hoch** (3-0)
Nur einmaliges Test-Guthaben (100 Credits), danach pro-Request (1 Credit/Identifikation, ab 0,05 €/Credit, Mindestbestellung 50 €), kein dauerhafter Free-Tier, kein self-hostbarer Erkennungspfad (nur ein quelloffener Apache-2.0 "Router"-Triage-Layer, der die Cloud-APIs **nicht** ersetzt). Verstößt gegen Constraint #2.
- https://www.kindwise.com/pricing · https://www.kindwise.com/plant-health

### Trainingsdaten-Lizenzlage

**T1 · iNaturalist-Content default CC-BY-NC** · Konfidenz: **hoch** (3-0)
Standardmäßig CC-BY-NC (nicht-kommerziell), solange der Nutzer nichts anderes wählt → als Trainings-/Referenzquelle für ein kommerzielles Produkt problematisch. Nur **CC0/CC-BY-gefilterte Teilmengen** kommerziell nutzbar. Das behauptete Pauschalverbot von KI-Training wurde **widerlegt (0-3)**.
- https://www.inaturalist.org/pages/terms

---

## 4. Widerlegte Behauptungen (adversarial gekillt)

Diese in der Recherche aufgetauchten Behauptungen wurden durch 2/3-Mehrheit **widerlegt** und sind **nicht** Grundlage der Empfehlung:

1. ✗ (1-2) „PlantCLEF-2024-Modell ist eindeutig CC-BY-NC" → Lizenzlage nicht abschließend geklärt, rechtlich prüfen.
2. ✗ (0-3) „PlantCLEF 2024 deckt über 800 Arten / 1,7 Mio Bilder ab" → falsche Zahlen (real: 7.806 Arten / ~1,4 Mio Bilder).
3. ✗ (1-2) „Kommerzielle Nutzung von Pl@ntNet-Daten ist erlaubt" → ShareAlike/Attribution-Pflichten bleiben.
4. ✗ (0-3) „iNaturalist verbietet jegliches KI-Training für kommerzielle Zwecke" → kein Pauschalverbot, sondern CC-BY-NC-Default.
5. ✗ (1-2) „iNaturalist-API unterliegt denselben CC-BY-NC-/KI-Trainingsverbots-Bedingungen".

---

## 5. Abgestufte Umsetzungsempfehlung (MVP → Ausbau)

### MVP — Self-hosted Artbestimmung (Aufgabe A)
1. **Inferenz-Microservice** analog `src/knowledge-service/` aufsetzen (ONNX Runtime, FastAPI).
2. **DINOv2 (Apache-2.0)** als ONNX-Embedding-Extraktor einbinden (CPU-fähig; Browser-Inferenz via ONNX Runtime Web/WebGPU als kostenlose Client-Offload-Option technisch tragbar).
3. **Referenz-Embeddings** der 210 Steckbriefe vorab indexieren — aus **lizenzkonform beschafften** Bildern (CC0/CC-BY, eigene Fotos), **nicht** aus CC-BY-SA-/CC-BY-NC-Quellen.
4. **ArangoDB-Vektorsuche** für Ähnlichkeits-Matching (Top-k Arten + Konfidenz).
5. Integration als **neuer Adapter** in der bestehenden `AdapterRegistry` (Enrichment-Pattern), schwere Inferenz per **Celery** offloaden.
6. **React-Upload-UI** + Ergebnis-Auswahl, gebunden an Species-Zuordnung.

### Ausbau Stufe 2 — Externer Fallback (Aufgabe A)
- Optionaler **Pl@ntNet-Free-Tier-Adapter** (≤500/Tag) bei niedriger Embedding-Konfidenz.
- Gated über **Consent-Record** (NFR-011) — Foto-Upload an Dritte erfordert Einwilligung; Auftragsverarbeitung dokumentieren.

### Ausbau Stufe 3 — IPM & Phänologie (Aufgaben B, C)
- **B:** Krankheits-/Schädlingserkennung via auf **PlantDoc** fine-getuntem Backbone, angebunden an REQ-010.
- **C:** Phänologie via eigenem Klassifikatorkopf auf DINOv2-Embeddings, trainiert auf projekteigenen Bildern entlang der REQ-003-Phasen.

---

## 6. DSGVO-Hinweise

- **Self-hosted Inferenz ist die DSGVO-seitig sicherste Variante** — Nutzerfotos verlassen die eigene Infrastruktur nicht.
- Bei **Pl@ntNet-Fallback**: Fotos werden nicht persistiert, aber Query-Metadaten gespeichert (keine Retention-Frist genannt) → **Einwilligung** (analog Consent-Record-Muster, NFR-011) + Auftragsverarbeitungsverhältnis erforderlich.
- Foto-Upload an **jeden** Dritt-Dienst nur opt-in und transparent.

---

## 7. Offene Punkte / Caveats

- **DINOv2-Lizenz** (Apache-2.0) vor Auslieferung im offiziellen `facebookresearch/dinov2`-Repo erneut verifizieren — hieran hängt die kommerzielle Nutzbarkeit.
- **CC-BY-NC der PlantCLEF-Gewichte** rechtlich abklären, falls fertige Klassifikatorgewichte je verwendet werden sollen (Embedding-only-Weg umgeht dies).
- **Treffergenauigkeit für Kamerplanters Zielarten** (Cannabis, tropische Zimmerpflanzen, Kultur-Kultivare) ist durch die Quellen **nicht belastbar belegt** — die großen Datensätze decken diese Arten nur teilweise ab. → **Eigene Evaluierung an den 210 Steckbriefen** zwingend.
- **Aufgabe C (Phänologie)** beruht auf Abwesenheit von Evidenz → gezielte Nachrecherche.
- Lizenz-/Preisangaben Stand **Juni 2026** aus Primärquellen — vor Implementierung re-validieren.

---

## Anhang — Recherche-Statistik

| Metrik | Wert |
|---|---|
| Such-Winkel | 6 |
| Quellen gefetcht | 27 |
| Claims extrahiert | 124 |
| Claims adversarial verifiziert | 25 |
| Bestätigt / Widerlegt | 20 / 5 |
| Nach Synthese (Findings) | 10 |
| Agenten-Calls | 110 |
