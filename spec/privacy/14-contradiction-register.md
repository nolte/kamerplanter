# SPEC-14 — Widerspruchsregister

```
Paket: spec/privacy · Version 1.1 · 2026-11-09
Zweck: Jeder im Paket, zwischen Paket und Specs/Code oder innerhalb der Specs gefundene Widerspruch
mit Auflösung, betroffenen Dokumenten und Regressions-/Abnahmetest. Status: aufgelöst (in allen
betroffenen Dokumenten geändert) · festgehalten (Auflösung liegt außerhalb: Spec-Änderung E16 oder
Rechtsentscheidung) · offen.
```

| W | Betroffene Anforderungen / Stellen | Konflikt | Fehlerhaft/unvollständig war | Auflösung | Geändert in | Test | Status |
|---|------------------------------------|----------|------------------------------|-----------|-------------|------|--------|
| W-01 | REQ-053 GP-FR-109 („Die Leitung **und die DSGVO-Kaskade** können die Freitextfelder … ersetzen“) vs. GP-NFR-055/E-16 („kein Freitextfeld wird bei der Kaskade geleert“); Code folgt E-16 (`test_privacy_engines.py:545`) | Spec-intern | GP-FR-109 | E-16 + Prüfwarteschlange (Kaskade **listet**, schwärzt nicht automatisch außer PRIV-239 hinter Flag) | `04` §5; E16 (Spec-Text) | TA-205, TA-239 | festgehalten (E16) |
| W-02 | PRIV-703 v1.0 (v0107 setzt registrierten Beat `privacy.consistency` voraus) vs. Roadmap (Beat in E15, P3; Migration in E04, P0) | Paket-intern | PRIV-703 | Vor-/Nachprüfung in die Migration; Beat-Minimalform nach E04 verschoben (DEC-28) | `09` §3, `08` §6, `12` E04/E15 | TA-701 (`verify`), TA-202 | aufgelöst |
| W-03 | `06` v1.0 §3 PRIV-401 (neue Organisationen werden gefragt, persönliche `none`) vs. `08` v1.0 §3.2 (`record_keeping = LEGACY` als Modell-Default für alle); Legacy-Default wäre stillschweigend Default neuer Mandanten geworden | Paket-intern | `08` §3.2 | kein Modell-Default; Anlagepfad verlangt Klassifizierung; v0108 stempelt Bestand (DEC-30) | `08` §3.2, `06` §1 PRIV-409, `03` PRIV-122, `09` §4 | TA-409, TA-630 | aufgelöst |
| W-04 | DEC-21 v1.0 („Default an bei Installationen, die bereits cachen“) vs. TDDDG § 25 Abs. 2 Nr. 2 „ausdrücklich gewünscht“ (L-11) | Paket vs. Recht | DEC-21 | Opt-in für alle, Übergang mit Dialog (DEC-29) | `07` §2.1, `09` §8, decision-log | TA-531, TA-532 | aufgelöst |
| W-05 | `04` v1.0 PRIV-225 (`defer` als Entscheidung), PRIV-226 (SLA nur Metrik) vs. Art. 17 Abs. 1 „unverzüglich“ | Paket vs. Recht | `04` §5 | Zustandsautomat; kein `defer`; SLA-Aktion (Flag) oder Eskalation (DEC-27) | `04` §5.1a/5.1b, `08` §3.7 | TA-239 | aufgelöst |
| W-06 | `04` v1.0 PRIV-223 (Obergrenze 5 000, Banner) vs. Art. 5 Abs. 2 / vollständige Entdeckung | Paket vs. Recht | PRIV-223 | Pagination mit Cursor, nur Eskalationsschwelle (DEC-27) | `04` §5.2, `08` §8 | TA-239, TA-810 | aufgelöst |
| W-07 | README v1.0 („ein LEG-Punkt blockiert nie das Engineering“) vs. Aufgabe/Art. 5 Abs. 2 (keine produktive Verarbeitung ohne Grundlage) | Paket-intern | README-Regel | drei Gates `engineering_allowed` / `deployment_allowed` / `processing_allowed`; Flags (DEC-32) | README, `06` §10, `08` §8a, decision-log §B | TA-631, TA-632 | aufgelöst |
| W-08 | Tombstone-Definition: `04` §2 ein Format `anon_`; `08` §2.2 Regex ein Format; Restore-Abgleich braucht alle Formate | Paket-intern | — (durch DEC-25 entstanden) | zwei Generationen `anon_`/`anon2_`; eine Regex in `privacy.py`; `is_tombstone` beidseitig; Restore prüft beide | `04` PRIV-238, `08` §2.2, `09` §6.4 | TA-200, TA-238, TA-710 | aufgelöst |
| W-09 | `erasure_replay_ledger` mit rohem `user_key` (`06` R-45, `08` §3.7, `09` §6 v1.0) vs. Datenminimierung; zirkuläre Begründung „Ledger muss im Dump sein, kann aber nicht“ | Paket-intern | Ledger-Design | Tombstone-Spiegel + Abgleich über `compute_tombstone_hash` wiederhergestellter `users` (DEC-26) | `09` §6, `08` §3.7, `02` §3.2, `06` R-45, `01` §3.2/§7 | TA-709, TA-710 | aufgelöst |
| W-10 | `docs/de/user-guide/privacy.md` („eine DSFA wurde durchgeführt“) vs. ADR-003 („DSFA-Frage offen“), keine DSFA im Repo | Spec/Doku | Doku | Satz entfernen; Vorprüfung `11` | E16 | TA-711 (Doku-Lane) | festgehalten (E16) |
| W-11 | `retention_tasks.py` Docstring „one year“ vs. `settings.py` 3 Jahre (R-06) | Code-intern | Docstring | korrigieren | E15 | — | festgehalten (E15) |
| W-12 | `01` ACV nennt `privacy.redact`; `05`/`08` kennen nur `privacy.review`; „Mandantenadministrator“ als Rollenname | Paket-intern | `01` §3.2, `05` Legende | eine Berechtigung `privacy.review`; Kurzform klargestellt | `01` §3.2, `05` §3 Legende | TA-307 | aufgelöst |
| W-13 | REQ-053 §13.2 („`treatment_applications` bleibt der Nachweis“) vs. unverifizierter Inhaltskatalog DVO 2023/564 (L-04) und § 11 Abs. 2 S. 2 PflSchG („unter Angabe des jeweiligen Anwenders“, L-01) bei geleertem Namen | Spec vs. Recht | REQ-053 §13.2 | Hilfsdokumentation bis V-04/V-06 (PRIV-413); Namensfrage LEG-04 | `06` §3.2, E16 | TA-413 | festgehalten (E16, LEG-04) |
| W-14 | R-45-Frist: `02` v1.0 „`BACKUP_RETENTION_DAYS + 5`“, `06` v1.0 „35 d“, `08` „expires_at + 5“ | Paket-intern | alle drei | R-45 = R-06 (3 J.) für den Spiegel (Tombstones, kein Rohschlüssel) | `02`, `06` §8, `08` §3.7, `09` §6.3 | TA-402 | aufgelöst |
| W-15 | NFR-011 R-16/R-17 und REQ-025 §3.1.3 Regel 2 (Collection-weite Pflichtaufbewahrung, Tombstone für `harvested_by_key`) vs. KCanG § 26 Abs. 1 (L-05: erntende Person keine Pflichtangabe), § 9/§ 10 (L-07: Eigenanbau ohne Pflicht) | Spec vs. Recht | NFR-011, REQ-025 | feldgenaue Zuordnung (`06` §3.2), PRIV-410/411 hinter Flag | `06` §3, `03` PRIV-122, E16 | TA-410 | festgehalten (E16; Flag bis LEG-03/17) |
| W-16 | `LEGAL_RETENTION_RULES` (Fristbeginn `applied_at`) vs. PflSchG § 11 Abs. 3 (1. Januar des Folgejahres, L-01) | Code vs. Recht | Code | PRIV-412 (DEC-31) | `06` §3.2, `03` PRIV-121 | TA-412 | festgehalten (E09) |
| W-17 | NFR-011 R-25 nennt „Art. 17(3) (berechtigtes Interesse: Anbauhistorie)“ als Grundlage | Spec vs. Recht | NFR-011 | Art. 17 Abs. 3 ist Ausnahme; Grundlage lit. b/f (DA-02) | `06` §2/§8, E16 | — | festgehalten (E16) |
| W-18 | `01` v1.0 §6.4 Fehlercode `account.erased` vs. `07`/`08` `account.closed` | Paket-intern | `01` | `account.closed` | `01` §6.4 | TA-520 | aufgelöst |
| W-19 | Issue #2517 („`CareConfirmation` … kept 5 years“) vs. Code (keine Aufbewahrung für `care_confirmations`; 5 J. = R-25 des abgeleiteten Ereignisses) | Issue vs. Code | Issue-Text | Faktenkorrektur in `06` §5, `02` §3.3 | bereits in v1.0 | — | aufgelöst (Issue-Kommentar durch Betreiber, nicht automatisiert) |
| W-20 | `05` Legende verwies auf PRIV-330 (existiert nicht) | Paket-intern | `05` | PRIV-316 | `05` §3 | — | aufgelöst |
| W-21 | `06` v1.0 §5 behauptete „objektiv geeignet“ (BAG) und „rechtlich unsicher nach C-34/21“ als Tatsachen ohne Primärquelle | Evidenz | `06` | als INFERRED gekennzeichnet; V-05, V-08 | `06` §5, `13` L-10, L-13 | — | aufgelöst (Kennzeichnung); offen (Verifikation) |
| W-22 | NFR-011 R-18 („Inspektionen, PflSchG § 11“) — § 11 nennt Inspektionen nicht (L-01) | Spec vs. Recht | NFR-011 R-18 | PRIV-413; LEG-03 benennt Vorschrift oder Klasse wird `shared_history` | `06` §3.2, §8 | — | festgehalten (LEG-03) |
| W-23 | REQ-023 §5b.1 („Backup-System … Cross-Tenant Read-Access“) vs. REQ-049 P4 / Code (kein Fachdatenzugriff) | Spec-intern | REQ-023 | Zeile angleichen | E16 | — | festgehalten (E16) |
| W-24 | REQ-025 §10 (Schlüssel `i18next`, `theme`, `redux_state`) vs. Code (`kamerplanter-lang`, `kamerplanter-theme`; kein `redux_state`); fehlende Schlüssel mit `user_key`/E-Mail | Spec vs. Code | REQ-025 §10 | Tabelle aus `07` §1 übernehmen (PRIV-500) | E16 | TA-500 | festgehalten (E16) |
| W-25 | Versions-/Fußzeilen-Drift (REQ-025 Header 1.40 / Footer 1.5; NFR-011 1.46 / 1.7; REQ-051 1.3 / 1.0) | Spec-intern | Fußzeilen | redaktionell | E16 | — | festgehalten (E16) |

**Regel für neue Widersprüche:** Ein Widerspruch wird hier eingetragen, bevor er in einem Dokument aufgelöst wird;
die Auflösung ändert **alle** betroffenen Dokumente in derselben Änderung und nennt den Test. Ein Widerspruch
wird nie durch Streichen der unbequemen Anforderung aufgelöst.
