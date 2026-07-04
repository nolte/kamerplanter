# CanG-Compliant Documentation for Cultivation Associations

If you run Kamerplanter for a **cultivation association** (cannabis social club) under the German Cannabis Act (CanG), you need to document cultivation without gaps, separate roles between the board, cultivation leads, and members, and observe statutory retention periods. This page doesn't introduce any new functionality — it shows how to combine building blocks that already exist in Kamerplanter — tenants, planting runs, harvest batches, the pre-harvest interval lock, and retention periods — for this purpose.

!!! warning "Not legal advice"
    This page describes which documentation features Kamerplanter offers you — it does not replace legal advice from a lawyer, tax advisor, or the responsible authority. Whether your association's structure and documentation satisfy the requirements of the Cannabis Act and the German Plant Protection Act (PflSchG) in your specific case should be clarified with a qualified professional.

---

## Overview: What This Page Chains Together

| Requirement | Relevant Kamerplanter Feature | Page(s) |
|-------------|-------------------------------|---------|
| Association as its own isolated area | Tenant of type "Organization" | [Tenants & Gardens](../user-guide/tenants.md) |
| Batch traceability | Planting run + harvest batch | [Planting Runs](../user-guide/planting-runs.md), [Harvest Management](../user-guide/harvest.md) |
| Pre-harvest interval compliance | Automatic pre-harvest interval lock at harvest | [Integrated Pest Management (IPM)](../user-guide/pest-management.md) |
| Retention periods | Retention matrix per CanG/PflSchG | [Data Retention & Anonymization](data-retention.md) |
| Role separation within the association | Admin / Grower / Viewer + location assignment | [Tenants & Gardens](../user-guide/tenants.md) |
| Central member sign-in | OIDC auto-join via the association's identity provider | [Tenants & Gardens](../user-guide/tenants.md), [Account & Sign-In](../user-guide/account.md) |

---

## 1. Set Up the Association as a Tenant

Create a dedicated [tenant](../user-guide/tenants.md) of type **Organization** for your cultivation association. All of the association's resources — locations, planting runs, harvests, treatments — are then fully isolated from your members' personal tenants: no member sees anyone else's private houseplants, and nobody outside the association sees the association's data.

Model your cultivation rooms (vegetative room, flowering room, drying room) as separate locations within this tenant — see [Locations & Substrates](../user-guide/locations-substrates.md).

## 2. Create and Trace Batches

Every grow starts as a [planting run](../user-guide/planting-runs.md): you group the plants of one room (e.g. "Flowering Room 1, Cycle 2026-03"), and record the variety, start date, and — for clones — the source plant. That already covers the first half of traceability (seed/cutting → plant) simply by using Kamerplanter as intended.

For harvest, you create a **harvest batch** per plant (menu **Harvest**) with harvest type, harvest date, fresh weight, and optionally your own **batch ID** (e.g. "HARVEST-2026-FLOWER1-003") — see [Harvest Management](../user-guide/harvest.md#creating-a-harvest-batch).

!!! note "The batch ID is a free-text field, not an automatic association-wide batch number"
    Kamerplanter does not automatically assign a sequential batch ID across the whole association — the field is a freely editable, optional identifier per harvest batch. To keep batch numbering consistent across the association, agree on your own naming scheme (e.g. room code + year + running number) and enter it manually for every harvest.

Afterwards, you record the quality assessment (appearance, aroma, color, defects, overall score) in the **Quality** tab of the same harvest batch — that's also part of the traceability chain.

## 3. Pre-Harvest Intervals and Treatment Records

Record every pest management treatment together with its pre-harvest interval under [Integrated Pest Management (IPM)](../user-guide/pest-management.md) as a master record for a treatment product. Once an application of that product has been documented for a plant, Kamerplanter automatically blocks the creation of a harvest batch for as long as the pre-harvest interval is still running. This applies regardless of whether a board member or a cultivation lead triggers the harvest. That's exactly the technical safety net that prevents an accidental harvest within the waiting period required by the Plant Protection Act (PflSchG).

!!! info "Recording a treatment application on a plant is currently API-only"
    There's no interface yet for recording a concrete treatment application (which product, when, on which plant) — an API endpoint is already available for this (see [For Technical Users: API Access](../user-guide/pest-management.md#for-technical-users-api-access)). Until the interface catches up, your association needs either someone technically capable of creating the entry via the API, or you need to additionally document applications in a separate log outside Kamerplanter until the pre-harvest interval lock takes technical effect.

## 4. Observe Retention Periods

Harvest data, treatment applications, and inspection records are subject to statutory minimum retention periods in Kamerplanter that **cannot** be shortened:

| Data Category | Minimum Period | Legal Basis |
|----------------|----------------|-------------|
| Harvest data (harvest batch, quality assessment, yield metrics) | 5 years | Cannabis Act (CanG) |
| Treatment applications | 3 years | Plant Protection Act (PflSchG) §11 |
| Inspection records | 3 years | Plant Protection Act (PflSchG) §11 |

If an association member submits an erasure request under Article 17 GDPR, Kamerplanter does **not** delete these records. Instead, it only removes the link to the person (`user_key` is cleared) — the harvest or treatment record itself remains until the statutory period expires. For the full retention matrix and the corresponding environment variables, see [Data Retention & Anonymization](data-retention.md#statutory-minimum-retention-periods).

## 5. Separate Roles Between Members

Kamerplanter distinguishes three roles per tenant — Admin, Grower, Viewer (see [Tenants & Gardens](../user-guide/tenants.md#roles-and-permissions)). For a cultivation association, the following mapping works well:

| Association Role | Kamerplanter Role | Rationale |
|-------------------|--------------------|-----------|
| Board / association leadership | Admin | Full access, member invitations, role management |
| Cultivation leads (head growers) | Grower, assigned to their room | Can edit plants, tasks, and harvests in their room |
| Treasurer, auditor, oversight person | Viewer | Full read access to all data, no changes |

Using [location-based write access](../user-guide/tenants.md#location-based-write-access), you assign a cultivation lead exactly to their own room — members of other rooms can then not accidentally edit it unless they are Admins themselves.

## 6. Central Member Sign-In via Single Sign-On (OIDC)

If your association already runs its own member directory (e.g. via Keycloak or another OpenID Connect provider), your platform administration can set it up as an additional sign-in provider — members then sign in through the association's own provider, as described in [Account & Sign-In](../user-guide/account.md#signing-in-with-google-github-or-another-provider). In addition, **OIDC auto-join** can be configured so new members automatically join your association's tenant on their first login instead of needing to be invited manually — see [Tenants & Gardens — Method 3: OIDC Auto-Join](../user-guide/tenants.md#inviting-members).

!!! info "Set up by the platform administration"
    Connecting your own identity provider via OIDC isn't something the association's board configures itself — it's set up by the technical administration of your Kamerplanter instance (self-hoster or operator).

---

## Limits of the Current Implementation

So you don't plan around features that don't exist yet: the following requirements, typical for cultivation associations, are currently **not** available.

!!! note "No dedicated authority export"
    There's no ready-made PDF or CSV export specifically for authority inspections (harvest log, treatment record, period summary in a single document) yet. During an inspection, you currently export the nutrient plan as a PDF (see [Print Views & Export](../user-guide/print-export.md)) and compile harvest and treatment data manually from the tabular harvest batch overview or via the API.

!!! note "No distribution log"
    Documenting which member received which amount and when from the association isn't modeled in Kamerplanter yet. For now, you need a separate log outside the system for this.

!!! note "No tamper-proof lock on later corrections"
    A harvest batch itself cannot be deleted once created — but notes and weight values can be edited afterwards at any time, and Kamerplanter doesn't log a change history of these corrections. If your association's compliance requirements call for a tamper-proof (immutable) record, additionally keep that information in your own immutable filing system.

---

## Frequently Asked Questions

??? question "Is Kamerplanter alone enough to fulfill all CanG documentation obligations?"
    Kamerplanter covers the core building blocks — batch traceability, the pre-harvest interval lock, retention periods, role separation. For complete authority reports and distribution logs, you currently still need supplementary, manual documentation outside the system (see [Limits of the Current Implementation](#limits-of-the-current-implementation)).

??? question "Can we model multiple cultivation rooms with different cultivation leads?"
    Yes. Model each room as its own location and assign it to the responsible member via location-based write access — see step 5 above.

??? question "What happens when a member leaves the association?"
    As long as the member is not the only Admin, they can leave the tenant at any time. Harvest and treatment data they documented remains with the association, since it belongs to the tenant, not the person.

---

## See Also

- [Tenants & Gardens](../user-guide/tenants.md)
- [Planting Runs](../user-guide/planting-runs.md)
- [Harvest Management](../user-guide/harvest.md)
- [Integrated Pest Management (IPM)](../user-guide/pest-management.md)
- [Data Retention & Anonymization](data-retention.md)
- [Account & Sign-In](../user-guide/account.md)
- [Privacy & GDPR](../user-guide/privacy.md)
- [Cannabis Grow Cycle: From Germination to Cure](journey-cannabis-cycle.md)
