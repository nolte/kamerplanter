# Glossary

This page explains the key terms you'll encounter in Kamerplanter and throughout this documentation — kept short and understandable without prior knowledge. Each entry links to the page where the topic is covered in depth.

!!! info "A static reference"
    This glossary page is a fixed list for looking things up, intended for developers and for quickly cross-referencing the documentation. For a searchable, AI-backed term explanation right inside the Kamerplanter application — including experience-level-adaptive explanations and related terms — use the [Terminology Glossary](../user-guide/glossary.md) in the app. <!-- REQ-035 -->

Terms are sorted alphabetically. Use the search box at the top of the page (or <kbd>Ctrl</kbd>/<kbd>Cmd</kbd> + <kbd>F</kbd>) to jump straight to a term.

---

### CalMag

Short for a calcium-magnesium supplement fertilizer. It matters most when you water with reverse-osmosis or rainwater, since that water lacks the natural calcium and magnesium hardness found in tap water. In Kamerplanter, CalMag is typically added before the other base fertilizers when mixing, to avoid unwanted precipitation with sulfates.

→ [Fertilization: CalMag](../user-guide/fertilization.md#calmag-when-and-how-much)

### CanG (German Cannabis Act)

German law regulating the controlled use of cannabis. Among other things, it requires certain harvest and cultivation data to be retained for audit purposes, even after an account is deleted. Kamerplanter accounts for the CanG when setting retention periods for harvest and treatment data.

→ [Privacy & GDPR: Data Retention and Retention Periods](../user-guide/privacy.md#data-retention-and-retention-periods)

### Companion Planting (Mischkultur)

Deliberately combining different plant species in a small space so they help rather than harm each other — for example through pest deterrence, better use of space, or attracting beneficial insects.

→ [Companion Planting & Crop Rotation](../guides/companion-planting.md)

### Crop Rotation (Fruchtfolge)

Deliberately alternating the botanical plant family grown in the same spot over several years. Crop rotation prevents one-sided depletion of soil nutrients and the buildup of family-specific pests and diseases.

→ [Companion Planting & Crop Rotation: Crop Rotation](../guides/companion-planting.md#crop-rotation)

### Daily Light Integral (DLI)

The total amount of light usable by a plant that falls on a surface over an entire day, measured in mol/m²/d. DLI is calculated from light intensity (PPFD) and lighting duration, which makes it more informative than a single instantaneous reading.

→ [Sensors and Measurements: Light Parameters](../user-guide/sensors.md#light-parameters)

### Deep Water Culture (DWC)

A hydroponic system in which a plant's roots hang permanently in an oxygen-enriched nutrient solution instead of growing in solid substrate. To keep the roots from suffocating, a DWC system typically needs an air pump and regular monitoring of dissolved oxygen.

→ [Tank Management: Understanding Tank Types](../user-guide/tanks.md#understanding-tank-types)

### Dormancy (Winterruhe)

The natural resting phase of perennial plants, usually during the cold season. During dormancy, growth as well as water and nutrient needs drop sharply — the plant requires much less care during this time.

→ [Growth Phases: Perennial Plants — Dormancy and Seasonal Cycles](../user-guide/growth-phases.md#perennial-plants-dormancy-and-seasonal-cycles)

### Drain-to-Waste

An irrigation strategy without recirculation: you deliberately water with a surplus (usually 10–30 % more than the substrate can hold), so runoff water drains from the bottom of the pot. This runoff is discarded rather than reused. The advantage: excess nutrient salts are flushed out instead of building up in the substrate.

→ [Mixing Nutrient Solutions: Runoff Analysis](../guides/nutrient-mixing.md#runoff-analysis)

### Electrical Conductivity (EC)

A measure of the concentration of dissolved nutrient salts in irrigation water, given in millisiemens per centimeter (mS/cm). The higher the EC value, the more nutrients are dissolved in the water — values too high can damage roots, values too low lead to deficiencies.

→ [Fertilization: Understanding the Basics](../user-guide/fertilization.md#understanding-the-basics)

### Fertigation

A blend of "fertilizer" and "irrigation": automatically delivering nutrient solution through the irrigation system, usually via a drip system and pump, instead of watering by hand with a can.

→ [Mixing Nutrient Solutions](../guides/nutrient-mixing.md), [Watering Log](../user-guide/watering-log.md)

### Growing Degree Days (GDD)

The sum of daily heat units above a species-specific base temperature. Growing degree days let you measure a plant's maturity progress by actual accumulated warmth rather than by calendar date — two identical cultivars mature faster in a warm location than in a cool one.

→ [GDD Calculation](../guides/gdd-calculation.md)

### Hysteresis

A deliberate gap between the on and off thresholds of an automatic rule. Hysteresis prevents an actuator (e.g. a humidifier) from rapidly switching on and off around a threshold that's just barely reached, which would strain the device and fail to produce a stable climate.

→ [Environment Control & Actuators: Configuring Hysteresis](../user-guide/actuator-control.md#configuring-hysteresis)

### Integrated Pest Management (IPM)

A three-tier approach to plant protection: prevention before monitoring (regular inspections), monitoring before intervention (treatment). The goal is to treat as rarely and as precisely as possible.

→ [Pest Management (IPM)](../user-guide/pest-management.md)

### InvenTree

A separate, open-source inventory management system that you can optionally run alongside Kamerplanter and link to your fertilizers, tanks and equipment. A "part" there is a single article (e.g. a spare pump). Link a Kamerplanter entity to a part ID and Kamerplanter keeps stock and consumption in sync with InvenTree automatically (stock sync) — you no longer have to update quantities by hand. The link is purely optional; without it, Kamerplanter keeps working without any limitation.

→ [Equipment & Inventory (InvenTree)](../user-guide/inventree.md)

### Model Context Protocol (MCP)

An open protocol that lets external AI language-model clients (e.g. Claude Desktop, Claude Code) call a system's structured "tools". Kamerplanter exposes a curated, machine-to-machine interface over MCP, restricted to service accounts — distinct from the AI assistant built into the app, which is meant for human users.

→ [MCP Server](../api/mcp-server.md)

### Nutrient Film Technique (NFT)

A hydroponic system in which a thin film of nutrient solution flows over the roots and then returns to a recirculation tank — unlike systems such as DWC, where the roots sit permanently in the nutrient solution.

→ [Tank Management: Understanding Tank Types](../user-guide/tanks.md#understanding-tank-types)

### OpenID Connect (OIDC)

An open standard for signing in via external providers such as Google, GitHub, or Apple, without Kamerplanter itself storing or managing your password.

→ [Account & Sign-In: Signing In with Google, GitHub or Another Provider](../user-guide/account.md#signing-in-with-google-github-or-another-provider)

### PflSchG (German Plant Protection Act)

German law regulating the use of plant protection products, including pre-harvest intervals and documentation requirements. Kamerplanter accounts for the PflSchG when setting retention periods for treatment data.

→ [Privacy & GDPR: Data Retention and Retention Periods](../user-guide/privacy.md#data-retention-and-retention-periods)

### Photosynthetic Photon Flux Density (PPFD)

A measure of the amount of photosynthetically usable light hitting a surface per second, given in µmol/m²/s. An important value for judging your plants' light supply — especially under artificial lighting.

→ [Sensors and Measurements: Light Parameters](../user-guide/sensors.md#light-parameters)

### Pre-Harvest Interval (PHI)

The legally required waiting period between the last application of a plant protection product and harvest. It protects consumers from residues in the harvested crop. Kamerplanter automatically blocks harvesting a plant while its pre-harvest interval is still running.

→ [Pest Management (IPM): Understanding and Monitoring Pre-Harvest Intervals](../user-guide/pest-management.md#understanding-and-monitoring-pre-harvest-intervals)

### RAG (Retrieval-Augmented Generation)

A technique in which an AI generates answers not only from trained knowledge, but also retrieves matching text snippets from a knowledge base and incorporates them into the answer. This makes responses more traceable and up to date, since they're grounded in concrete sources.

→ [AI Assistant](../user-guide/ai-assistant.md), [Understanding the RAG Knowledge Base](../guides/rag-knowledge-base.md)

### Succession Sowing (Sukzession)

A gardening strategy where the same crop is sown in several batches staggered over time — for example, radishes every two weeks instead of all at once. This spreads the harvest over a longer period instead of it arriving all at once.

### USDA Hardiness Zone

A classification of locations by their average annual minimum temperature, into zones from 1 (very cold) to 13 (very mild), developed by the U.S. Department of Agriculture (USDA). Kamerplanter uses this format to automatically check whether a plant species can overwinter outdoors at your location.

→ [Climate Zones & Hardiness](../guides/climate-zones.md), [Locations & Substrates](../user-guide/locations-substrates.md)

### Vapor Pressure Deficit (VPD)

A metric indicating how much additional moisture the air could still absorb at the current temperature before becoming saturated. VPD is one of the most important climate values for healthy plant growth: too low, and it favors fungal disease; too high, and the plant loses too much water through its leaves and partially shuts down photosynthesis.

→ [VPD Optimization](../guides/vpd-optimization.md), [Growth Phases: VPD Target](../user-guide/growth-phases.md#vpd-target-vapor-pressure-deficit)

### Vernalization

The cold exposure that some biennial plants (e.g. carrots or onions grown for seed) require for a species-specific minimum number of days before they can flower the following year. Without this cold exposure, flowering does not occur.

→ [Growth Phases: Automatic Phase Transitions](../user-guide/growth-phases.md#automatic-phase-transitions)

---

## See Also

- [Getting Started](../getting-started/index.md)
- [User Guide](../user-guide/index.md)
- [My Plant Doesn't Look Well — Symptom Diagnosis](../user-guide/plant-health-troubleshooting.md)
