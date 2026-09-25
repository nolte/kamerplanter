# Issue #1791 — Vorab-Analyse (issue-orchestrate)

- Issue: https://github.com/nolte/kamerplanter/issues/1791 (Autor `nolte` = Repository-Owner → vertrauenswürdig)
- Klassifikation: `security` (sekundär `spec-change`) — eine irreversible Aktion ohne Rollen- und Step-up-Schranke.
- Route: **direkt** (ein Ergebnis, ein PR-Strang, kein Roadmap-Eintrag). Betreiberfreigabe 2026-09-25: alle Gates vorab freigegeben.
- Anforderungs-Gate: Betreiber-Override — die Akzeptanzkriterien des Issues sind konkret (Rolle + Step-up + Route-Tests je Kombination + Spec-Abgleich); kein `requirements-elicit`.

## Gemessener Ist-Zustand (established)

- `DELETE /api/v1/t/{slug}` → `require_admin_scope(AdminScope.MANAGEMENT)` allein (`src/backend/app/api/v1/tenants/router.py:101-114`). Ein `viewer` mit `management` erreicht `TenantService.delete_tenant`.
- `DELETE /api/v1/admin/platform/tenants/{key}` → `require_platform_admin` (`src/backend/app/api/v1/admin/platform/router.py:231-251`), kein Step-up.
- `TenantService.delete_tenant(tenant_key, *, origin, now)` (`src/backend/app/domain/services/tenant_service.py:284`) prüft keinen Aufrufer — die Schranke liegt nur am Router.
- Kontolöschung (REQ-394): `PrivacyService.request_erasure` verlangt das Passwort nur bei `password_hash is not None`; föderierte Konten ohne Step-up (`privacy_service.py:526-531`), 401 bei Fehlschlag.
- Frontend: `deleteTenant(slug)` (`src/frontend/src/api/endpoints/tenants.ts:38`) hat **keinen** UI-Aufrufer; `AdminEditTenantPage` löscht über `deleteAdminTenant` mit einem Bestätigungs-Alert ohne Step-up.

## Entscheidung

| Frage | Entscheidung | Grund |
|---|---|---|
| Rolle (Mandantenroute) | `management` **und** `lead` (Schnittmenge beider Achsen) | REQ-049 §2.3 Irreversibilitätsgrenze = Leitung; REQ-024/049 §2.4 Verwaltung. Schnittmenge ist keine Vermischung der Achsen. |
| Eigentümer | **nicht** verlangt | REQ-049 kennt keine Eigentümerrolle; `owner_user_key` ist Herkunft. Eine Eigentümer-Pflicht machte einen Garten unlöschbar, sobald der Gründer geht. |
| Plattform-Admin | bleibt berechtigt (echte `lead`-Mitgliedschaft in `platform`, im Service nachgeprüft), gleicher Step-up | Betriebsweg; irreversibel für jeden Aufrufer. |
| Step-up | Slug-Echo (`confirm_slug`) für alle; zusätzlich aktuelles Passwort, wenn das Konto eins hat | REQ-394-Muster; föderierte Konten haben kein lokales Geheimnis → Slug-Echo ist ihre bewusste Bestätigung (Rest-Lücke als Folge-Issue: OIDC-Re-Auth). |
| Dienstkonten | verweigert (403) | Schlüssel-Auth ist nicht re-authentifizierbar; REQ-023: keine interaktive Handlung. |
| Durchsetzung | im Service (`delete_tenant(..., requester=..., confirmation=...)`, keyword-only ohne Default) | beide Routen teilen denselben Pfad. |
| Audit | `TenantErasureRecord.requested_by_subject` (`log_subject`) + `step_up`; Logzeile `tenant_erasure.authorized` | kein Klartext-Kontoschlüssel im Datensatz, der den Mandanten überlebt. |
| Fehlercodes | 403 Rolle/Scope/Dienstkonto, 422 Slug falsch, 401 Passwort falsch/fehlend | 401 wie `/privacy/erasure`. |

## Arbeitspakete

| ID | Paket | Akzeptanz | Spezialist |
|---|---|---|---|
| WP1 | Backend: Prädikat + Service-Gate + Schemas + Router beider Routen + Audit | Route-Tests je Kombination rot-zuerst, dann grün | Generalist (Präzedenz #1797; `fullstack-developer` passt, Schranke wird aber vom Orchestrator rot-zuerst gebaut) |
| WP2 | Frontend: `AdminEditTenantPage` Step-up-Dialog (Slug + Passwort fail-closed), API-Signaturen, i18n DE/EN | vitest rot-zuerst | Generalist |
| WP3 | Spec: REQ-024 §1a.2/API/AK, REQ-049 §2.4/§4.2 | Text stimmt mit Code | Generalist |
| WP4 | Doku (Mandanten/Admin) | mkdocs strict | `mkdocs-documentation` |
| WP5 | Review | Findings disponiert | `nolte-engineering:code-security-reviewer`, `/code-review medium` |

Abhängigkeit: WP1 → WP2 → WP3 → WP4 → WP5.
