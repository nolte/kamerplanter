#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────
# import_monstera.sh — Import Monstera deliciosa + dependencies via REST API
#
# Imports: Araceae family, Monstera deliciosa species, lifecycle config,
#          3 cultivars, IPM entities (pest, diseases, treatments, biologicals),
#          Gardol fertilizer, nutrient plan with 4 phase entries.
#
# Usage:  ./scripts/import_monstera.sh [BASE_URL]
# Default BASE_URL: http://localhost:8000
# ──────────────────────────────────────────────────────────────────────
set -euo pipefail

BASE="${1:-http://localhost:8000}"
API="${BASE}/api/v1"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

ok()   { echo -e "${GREEN}✓${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; exit 1; }
info() { echo -e "${CYAN}→${NC} $1"; }
warn() { echo -e "${YELLOW}⚠${NC} $1"; }

# Extract .key from JSON response
extract_key() { echo "$1" | python3 -c "import sys,json; print(json.load(sys.stdin)['key'])"; }

# ── Step 0: Connectivity check ────────────────────────────────────────
info "Checking backend connectivity..."
curl -sf -o /dev/null "${API}/nutrient-plans" \
  || fail "Backend not reachable at ${BASE}"
ok "Backend reachable at ${BASE}"

# Helper for requests (no auth required for resource endpoints)
post() {
  local url="$1" data="$2" label="$3"
  local resp
  resp=$(curl -sf -X POST "$url" -H "Content-Type: application/json" -d "$data") \
    || fail "POST $label failed"
  echo "$resp"
}

get() {
  local url="$1"
  curl -sf -X GET "$url"
}

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Teil 1: Stammdaten (Family, Species, Lifecycle, Cultivars)"
echo "════════════════════════════════════════════════════════════════"

# ── Step 1: BotanicalFamily — Araceae ─────────────────────────────────
info "Creating BotanicalFamily: Araceae..."
FAMILY_RESP=$(post "${API}/botanical-families" '{
  "name": "Araceae",
  "common_name_de": "Aronstabgew\u00e4chse",
  "common_name_en": "Arum family",
  "order": "Alismatales",
  "typical_nutrient_demand": "medium",
  "nitrogen_fixing": false,
  "typical_root_depth": "shallow",
  "frost_tolerance": "sensitive",
  "typical_growth_forms": ["vine"],
  "pollination_type": ["insect"]
}' "BotanicalFamily Araceae")
FAMILY_KEY=$(extract_key "$FAMILY_RESP")
ok "BotanicalFamily created: key=${FAMILY_KEY}"

# ── Step 2: Species — Monstera deliciosa ──────────────────────────────
info "Creating Species: Monstera deliciosa..."
SPECIES_RESP=$(post "${API}/species" '{
  "scientific_name": "Monstera deliciosa",
  "common_names": ["Fensterblatt", "Swiss Cheese Plant", "Monstera"],
  "family_key": "'"${FAMILY_KEY}"'",
  "genus": "Monstera",
  "hardiness_zones": ["10a", "10b", "11a", "11b", "12a", "12b"],
  "native_habitat": "Tropische Regenwaelder Suedmexikos bis Panama",
  "growth_habit": "vine",
  "root_type": "fibrous",
  "allelopathy_score": 0.0
}' "Species Monstera deliciosa")
SPECIES_KEY=$(extract_key "$SPECIES_RESP")
ok "Species created: key=${SPECIES_KEY}"

# ── Step 3: LifecycleConfig ───────────────────────────────────────────
info "Creating LifecycleConfig: perennial, day_neutral..."
LIFECYCLE_RESP=$(post "${API}/lifecycle-configs" '{
  "species_key": "'"${SPECIES_KEY}"'",
  "cycle_type": "perennial",
  "typical_lifespan_years": 40,
  "dormancy_required": false,
  "vernalization_required": false,
  "photoperiod_type": "day_neutral"
}' "LifecycleConfig")
LIFECYCLE_KEY=$(extract_key "$LIFECYCLE_RESP")
ok "LifecycleConfig created: key=${LIFECYCLE_KEY}"

# ── Step 4: Cultivars (3x) ───────────────────────────────────────────
info "Creating Cultivar: Thai Constellation..."
CV1_RESP=$(post "${API}/cultivars" '{
  "name": "Thai Constellation",
  "species_key": "'"${SPECIES_KEY}"'",
  "breeder": "Tissue Culture Lab Thailand",
  "breeding_year": 2010,
  "traits": ["compact", "ornamental"]
}' "Cultivar Thai Constellation")
CV1_KEY=$(extract_key "$CV1_RESP")
ok "Cultivar Thai Constellation: key=${CV1_KEY}"

info "Creating Cultivar: Albo Variegata..."
CV2_RESP=$(post "${API}/cultivars" '{
  "name": "Albo Variegata",
  "species_key": "'"${SPECIES_KEY}"'",
  "traits": ["ornamental"]
}' "Cultivar Albo Variegata")
CV2_KEY=$(extract_key "$CV2_RESP")
ok "Cultivar Albo Variegata: key=${CV2_KEY}"

info "Creating Cultivar: Borsigiana..."
CV3_RESP=$(post "${API}/cultivars" '{
  "name": "Borsigiana",
  "species_key": "'"${SPECIES_KEY}"'",
  "traits": ["compact"]
}' "Cultivar Borsigiana")
CV3_KEY=$(extract_key "$CV3_RESP")
ok "Cultivar Borsigiana: key=${CV3_KEY}"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Teil 2: IPM (Pest, Diseases, Treatments)"
echo "════════════════════════════════════════════════════════════════"

# ── Step 5: IPM — New entities ────────────────────────────────────────
# Note: Spider Mites, Thrips, Mealybug, Fungus Gnats, Root Rot, Neem Oil,
#       Phytoseiulus persimilis, Sticky Traps are assumed to exist from seed data.
#       We create only the missing entities here.

info "Creating Pest: Schildlaeuse (Coccoidea)..."
PEST_SCALE_RESP=$(post "${API}/ipm/pests" '{
  "scientific_name": "Coccoidea",
  "common_name": "Schildl\u00e4use (Scale)",
  "pest_type": "insect",
  "detection_difficulty": "medium",
  "description": "Braune H\u00f6cker an Stielen und Blattadern, Honigtau-Ausscheidung, Russtaupilze als Sekund\u00e4rbefall. Bei Monstera vor allem an Blattstielen und Blattunterseiten."
}' "Pest Schildlaeuse")
PEST_SCALE_KEY=$(extract_key "$PEST_SCALE_RESP")
ok "Pest Schildlaeuse: key=${PEST_SCALE_KEY}"

info "Creating Disease: Blattfleckenkrankheit..."
DIS_LEAFSPOT_RESP=$(post "${API}/ipm/diseases" '{
  "scientific_name": "Leaf Spot (various)",
  "common_name": "Blattfleckenkrankheit (Leaf Spot)",
  "pathogen_type": "fungal",
  "incubation_period_days": 7,
  "environmental_triggers": ["high_humidity", "poor_airflow", "wet_leaves"],
  "affected_plant_parts": ["leaf"],
  "description": "Braune oder schwarze Flecken mit gelbem Hof auf Bl\u00e4ttern. Ausl\u00f6ser: hohe Luftfeuchtigkeit, schlechte Luftzirkulation, nasse Bl\u00e4tter."
}' "Disease Blattfleckenkrankheit")
DIS_LEAFSPOT_KEY=$(extract_key "$DIS_LEAFSPOT_RESP")
ok "Disease Blattfleckenkrankheit: key=${DIS_LEAFSPOT_KEY}"

info "Creating Disease: Russtaupilze..."
DIS_SOOTYMOLD_RESP=$(post "${API}/ipm/diseases" '{
  "scientific_name": "Capnodiales (Sooty Mold)",
  "common_name": "Russtaupilze (Sooty Mold)",
  "pathogen_type": "fungal",
  "incubation_period_days": 5,
  "environmental_triggers": ["pest_honeydew"],
  "affected_plant_parts": ["leaf"],
  "description": "Schwarzer Belag auf Bl\u00e4ttern, Sekund\u00e4rbefall nach Sch\u00e4dlingsbefall mit Honigtau (Schildl\u00e4use, Wolll\u00e4use). L\u00f6st sich durch Bek\u00e4mpfung des Prim\u00e4rsch\u00e4dlings."
}' "Disease Russtaupilze")
DIS_SOOTYMOLD_KEY=$(extract_key "$DIS_SOOTYMOLD_RESP")
ok "Disease Russtaupilze: key=${DIS_SOOTYMOLD_KEY}"

# Treatments
info "Creating Treatment: Schmierseife..."
TRT_SOAP_RESP=$(post "${API}/ipm/treatments" '{
  "name": "Schmierseife (Kaliseife)",
  "treatment_type": "biological",
  "active_ingredient": "Kaliumsalze von Fetts\u00e4uren",
  "application_method": "spray",
  "safety_interval_days": 0,
  "dosage_per_liter": 15.0,
  "description": "1-2% L\u00f6sung (10-20 ml/L) auf befallene Pflanzenteile spr\u00fchen. Wirkt gegen weichh\u00e4utige Insekten (Blattl\u00e4use, Wolll\u00e4use, Spinnmilben). Kontaktwirkung, keine Residualwirkung."
}' "Treatment Schmierseife")
TRT_SOAP_KEY=$(extract_key "$TRT_SOAP_RESP")
ok "Treatment Schmierseife: key=${TRT_SOAP_KEY}"

info "Creating Treatment: Alkohol-Abwischen..."
TRT_ALCOHOL_RESP=$(post "${API}/ipm/treatments" '{
  "name": "Alkohol-Abwischen",
  "treatment_type": "mechanical",
  "active_ingredient": "Isopropanol 70%",
  "application_method": "manual",
  "safety_interval_days": 0,
  "description": "Wattestab mit 70% Isopropanol auf befallene Stellen tupfen. Effektiv gegen Wolll\u00e4use und Schildl\u00e4use. Einzelbehandlung, nicht grossfl\u00e4chig auftragen."
}' "Treatment Alkohol-Abwischen")
TRT_ALCOHOL_KEY=$(extract_key "$TRT_ALCOHOL_RESP")
ok "Treatment Alkohol-Abwischen: key=${TRT_ALCOHOL_KEY}"

info "Creating Treatment: Blaetter abbrausen..."
TRT_SHOWER_RESP=$(post "${API}/ipm/treatments" '{
  "name": "Bl\u00e4tter abbrausen",
  "treatment_type": "cultural",
  "application_method": "manual",
  "safety_interval_days": 0,
  "description": "Pflanze alle 2-4 Wochen unter warmer Dusche (20-25\u00b0C) abbrausen. Entfernt Spinnmilben, Staub und h\u00e4lt Bl\u00e4tter sauber. Pr\u00e4ventiv und kurativ."
}' "Treatment Blaetter abbrausen")
TRT_SHOWER_KEY=$(extract_key "$TRT_SHOWER_RESP")
ok "Treatment Blaetter abbrausen: key=${TRT_SHOWER_KEY}"

# Biological controls
info "Creating Treatment: Amblyseius cucumeris..."
TRT_AMBLY_RESP=$(post "${API}/ipm/treatments" '{
  "name": "Amblyseius cucumeris",
  "treatment_type": "biological",
  "application_method": "release",
  "safety_interval_days": 0,
  "description": "Raubmilbe gegen Thrips-Larven. 50-100 St\u00fcck/m\u00b2 (Streubeutel). Etablierungszeit 14-28 Tage. Ben\u00f6tigt >60% Luftfeuchtigkeit."
}' "Treatment Amblyseius cucumeris")
TRT_AMBLY_KEY=$(extract_key "$TRT_AMBLY_RESP")
ok "Treatment Amblyseius cucumeris: key=${TRT_AMBLY_KEY}"

info "Creating Treatment: Cryptolaemus montrouzieri..."
TRT_CRYPTO_RESP=$(post "${API}/ipm/treatments" '{
  "name": "Cryptolaemus montrouzieri (Australischer Marienk\u00e4fer)",
  "treatment_type": "biological",
  "application_method": "release",
  "safety_interval_days": 0,
  "description": "Frisst Wolll\u00e4use und deren Eier. 2-5 St\u00fcck/m\u00b2. Etablierungszeit 14-21 Tage. Optimal bei 20-25\u00b0C."
}' "Treatment Cryptolaemus montrouzieri")
TRT_CRYPTO_KEY=$(extract_key "$TRT_CRYPTO_RESP")
ok "Treatment Cryptolaemus montrouzieri: key=${TRT_CRYPTO_KEY}"

info "Creating Treatment: Chrysoperla carnea..."
TRT_CHRYSO_RESP=$(post "${API}/ipm/treatments" '{
  "name": "Chrysoperla carnea (Florfliegenlarve)",
  "treatment_type": "biological",
  "application_method": "release",
  "safety_interval_days": 0,
  "description": "Generalisten-R\u00e4uber gegen Blattl\u00e4use, Wolll\u00e4use, Thrips. 5-10 St\u00fcck/m\u00b2. Etablierungszeit ca. 14 Tage. Larven sind extrem gefrässig."
}' "Treatment Chrysoperla carnea")
TRT_CHRYSO_KEY=$(extract_key "$TRT_CHRYSO_RESP")
ok "Treatment Chrysoperla carnea: key=${TRT_CHRYSO_KEY}"

info "Creating Treatment: Steinernema feltiae..."
TRT_NEMATODE_RESP=$(post "${API}/ipm/treatments" '{
  "name": "Steinernema feltiae (Nematoden)",
  "treatment_type": "biological",
  "application_method": "drench",
  "safety_interval_days": 0,
  "description": "Insektenpathogene Nematoden gegen Trauermuecken-Larven. Giessbehandlung: Nematoden in Giesswasser aufl\u00f6sen und Substrat tr\u00e4nken. Wirkung nach 7-14 Tagen. Bodentemperatur min. 12\u00b0C."
}' "Treatment Steinernema feltiae")
TRT_NEMATODE_KEY=$(extract_key "$TRT_NEMATODE_RESP")
ok "Treatment Steinernema feltiae: key=${TRT_NEMATODE_KEY}"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Teil 3: Fertilizer"
echo "════════════════════════════════════════════════════════════════"

# ── Step 6: Fertilizer — Gardol Gruenpflanzenduenger ──────────────────
info "Creating Fertilizer: Gardol Gruenpflanzenduenger..."
FERT_RESP=$(post "${API}/fertilizers" '{
  "product_name": "Gr\u00fcnpflanzend\u00fcnger",
  "brand": "Gardol (Bauhaus)",
  "fertilizer_type": "base",
  "is_organic": false,
  "tank_safe": false,
  "recommended_application": "drench",
  "npk_ratio": [6.0, 4.0, 6.0],
  "ec_contribution_per_ml": 0.06,
  "mixing_priority": 20,
  "ph_effect": "neutral",
  "bioavailability": "immediate",
  "storage_temp_min": 5.0,
  "storage_temp_max": 30.0,
  "notes": "Mineralischer Basisd\u00fcnger f\u00fcr Gr\u00fcnpflanzen/Blattpflanzen. Zimmerpflanzen: 1/4 Dosierkappe auf 5L, w\u00f6chentlich M\u00e4rz-Oktober. NPK 6-4-6, stickstoffbetont f\u00fcr Blattwachstum. Bauhaus Eigenmarke. EC-Beitrag gesch\u00e4tzt (~0,06 mS/cm pro ml/L)."
}' "Fertilizer Gardol")
FERT_KEY=$(extract_key "$FERT_RESP")
ok "Fertilizer Gardol: key=${FERT_KEY}"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Teil 4: NutrientPlan + Phase Entries"
echo "════════════════════════════════════════════════════════════════"

# ── Step 7: NutrientPlan ──────────────────────────────────────────────
info "Creating NutrientPlan: Monstera deliciosa — Gardol Gruenpflanzenduenger..."
PLAN_RESP=$(post "${API}/nutrient-plans" '{
  "name": "Monstera deliciosa \u2014 Gardol Gr\u00fcnpflanzend\u00fcnger",
  "description": "Ganzjahresplan f\u00fcr Monstera deliciosa in Erdsubstrat. Einzeld\u00fcnger-Konzept mit Gardol Gr\u00fcnpflanzend\u00fcnger (NPK 6-4-6). Saisonaler Rhythmus: M\u00e4rz\u2013Oktober D\u00fcngung, November\u2013Februar Pause.",
  "recommended_substrate_type": "soil",
  "author": "Kamerplanter Referenzdaten",
  "is_template": true,
  "version": "1.2",
  "tags": ["monstera", "zimmerpflanze", "gruenpflanze", "gardol", "erde", "indoor", "anfaenger"],
  "water_mix_ratio_ro_percent": null,
  "cycle_restart_from_sequence": 3,
  "watering_schedule": {
    "schedule_mode": "interval",
    "interval_days": 7,
    "preferred_time": "09:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  }
}' "NutrientPlan")
PLAN_KEY=$(extract_key "$PLAN_RESP")
ok "NutrientPlan created: key=${PLAN_KEY}"

# ── Step 8: Phase Entries (4x) ────────────────────────────────────────

info "Creating PhaseEntry 1/4: GERMINATION (Bewurzelung, W1-4)..."
PE1_RESP=$(post "${API}/nutrient-plans/${PLAN_KEY}/entries" '{
  "phase_name": "germination",
  "sequence_order": 1,
  "week_start": 1,
  "week_end": 4,
  "is_recurring": false,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Keine D\u00fcngung. Steckling nur mit klarem Wasser gie\u00dfen. Substrat feucht halten, nicht nass. 3-Tage-Intervall gilt f\u00fcr kleine T\u00f6pfe (8\u201310 cm) bei 22\u201325 \u00b0C. In k\u00fchlen/feuchten R\u00e4umen auf 5\u20137 Tage verl\u00e4ngern. Fingerprobe vorrangig. Bewurzelung in Wasser: Gie\u00dfplan entf\u00e4llt.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 3,
    "preferred_time": "09:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-bewurzelung",
      "label": "Nur Wasser (Bewurzelung)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Nur klares Wasser, kein D\u00fcnger. DRENCH = von oben gie\u00dfen.",
      "target_ec_ms": null,
      "target_ph": 6.0,
      "fertilizer_dosages": [],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.10
      }
    }
  ]
}' "PhaseEntry GERMINATION")
PE1_KEY=$(extract_key "$PE1_RESP")
ok "PhaseEntry GERMINATION: key=${PE1_KEY}"

info "Creating PhaseEntry 2/4: SEEDLING (Juvenil, W5-16)..."
PE2_RESP=$(post "${API}/nutrient-plans/${PLAN_KEY}/entries" '{
  "phase_name": "seedling",
  "sequence_order": 2,
  "week_start": 5,
  "week_end": 16,
  "is_recurring": false,
  "npk_ratio": [1.0, 1.0, 1.0],
  "calcium_ppm": 40.0,
  "magnesium_ppm": 20.0,
  "notes": "Halbe Dosis alle 14 Tage. Pflanze baut Wurzelsystem und erste Bl\u00e4tter auf. Eisenbedarf ca. 1 ppm (Steckbrief). Bei trockener Heizungsluft zwischen D\u00fcngeterminen mit klarem Wasser befeuchten.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 14,
    "preferred_time": "09:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "drench-giessduengung",
      "label": "Gie\u00dfd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "D\u00fcnger ins Gie\u00dfwasser einr\u00fchren, nur auf feuchtes Substrat gie\u00dfen.",
      "target_ec_ms": 0.6,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {
          "fertilizer_key": "'"${FERT_KEY}"'",
          "ml_per_liter": 2.0,
          "optional": false
        }
      ],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.3
      }
    }
  ]
}' "PhaseEntry SEEDLING")
PE2_KEY=$(extract_key "$PE2_RESP")
ok "PhaseEntry SEEDLING: key=${PE2_KEY}"

info "Creating PhaseEntry 3/4: VEGETATIVE (Aktives Wachstum, W17-48)..."
PE3_RESP=$(post "${API}/nutrient-plans/${PLAN_KEY}/entries" '{
  "phase_name": "vegetative",
  "sequence_order": 3,
  "week_start": 17,
  "week_end": 48,
  "is_recurring": true,
  "npk_ratio": [1.5, 1.0, 1.5],
  "calcium_ppm": 80.0,
  "magnesium_ppm": 40.0,
  "notes": "Volle Dosis w\u00f6chentlich (April\u2013September), halbe Dosis 14-t\u00e4gig (M\u00e4rz, Oktober). NPK 1,5:1:1,5 = Gardol-Produktrealit\u00e4t. Ca/Mg aus Leitungswasser, nicht aus Gardol. Bei weichem Wasser/RO CalMag-Supplement erforderlich. Fe 2 ppm Richtwert. Alle 6\u20138 Wochen Salzsp\u00fclung.",
  "delivery_channels": [
    {
      "channel_id": "drench-giessduengung",
      "label": "Gie\u00dfd\u00fcngung (Gie\u00dfkanne)",
      "application_method": "drench",
      "enabled": true,
      "notes": "D\u00fcnger ins Gie\u00dfwasser einr\u00fchren, nur auf feuchtes Substrat gie\u00dfen.",
      "target_ec_ms": 1.0,
      "target_ph": 6.0,
      "fertilizer_dosages": [
        {
          "fertilizer_key": "'"${FERT_KEY}"'",
          "ml_per_liter": 4.0,
          "optional": false
        }
      ],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.5
      }
    }
  ]
}' "PhaseEntry VEGETATIVE")
PE3_KEY=$(extract_key "$PE3_RESP")
ok "PhaseEntry VEGETATIVE: key=${PE3_KEY}"

info "Creating PhaseEntry 4/4: DORMANCY (Ruheperiode, W49-66)..."
PE4_RESP=$(post "${API}/nutrient-plans/${PLAN_KEY}/entries" '{
  "phase_name": "dormancy",
  "sequence_order": 4,
  "week_start": 49,
  "week_end": 66,
  "is_recurring": true,
  "npk_ratio": [0.0, 0.0, 0.0],
  "calcium_ppm": null,
  "magnesium_ppm": null,
  "notes": "Saisonale Ruhephase November\u2013Februar (kulturpraktisch, keine obligate Dormanz). Keine D\u00fcngung. 12-Tage-Intervall bei 18\u201322 \u00b0C, bei 15\u201318 \u00b0C auf 14 Tage verl\u00e4ngern. Fingerprobe: obere 4\u20135 cm trocken = gie\u00dfen. Substratsp\u00fclung einmalig im November.",
  "watering_schedule_override": {
    "schedule_mode": "interval",
    "interval_days": 12,
    "preferred_time": "09:00",
    "application_method": "drench",
    "reminder_hours_before": 2,
    "times_per_day": 1
  },
  "delivery_channels": [
    {
      "channel_id": "wasser-dormancy",
      "label": "Nur Wasser (Ruheperiode)",
      "application_method": "drench",
      "enabled": true,
      "notes": "Nur klares Wasser, kein D\u00fcnger. Reduziertes Volumen.",
      "target_ec_ms": null,
      "target_ph": 6.0,
      "fertilizer_dosages": [],
      "method_params": {
        "method": "drench",
        "volume_per_feeding_liters": 0.3
      }
    }
  ]
}' "PhaseEntry DORMANCY")
PE4_KEY=$(extract_key "$PE4_RESP")
ok "PhaseEntry DORMANCY: key=${PE4_KEY}"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Teil 5: Verification"
echo "════════════════════════════════════════════════════════════════"

# ── Verification ──────────────────────────────────────────────────────

info "Verifying BotanicalFamily..."
get "${API}/botanical-families/${FAMILY_KEY}" > /dev/null && ok "GET botanical-families/${FAMILY_KEY}" || fail "Verification failed: BotanicalFamily"

info "Verifying Species..."
get "${API}/species/${SPECIES_KEY}" > /dev/null && ok "GET species/${SPECIES_KEY}" || fail "Verification failed: Species"

info "Verifying Cultivars..."
CULTIVAR_COUNT=$(get "${API}/cultivars?species_key=${SPECIES_KEY}" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
[ "$CULTIVAR_COUNT" -ge 3 ] && ok "Cultivars: ${CULTIVAR_COUNT} found (expected >= 3)" || fail "Cultivars: only ${CULTIVAR_COUNT} found"

info "Verifying Fertilizer..."
get "${API}/fertilizers/${FERT_KEY}" > /dev/null && ok "GET fertilizers/${FERT_KEY}" || fail "Verification failed: Fertilizer"

info "Verifying NutrientPlan (cycle_restart_from_sequence)..."
PLAN_CHECK=$(get "${API}/nutrient-plans/${PLAN_KEY}")
CYCLE_RESTART=$(echo "$PLAN_CHECK" | python3 -c "import sys,json; print(json.load(sys.stdin).get('cycle_restart_from_sequence'))")
[ "$CYCLE_RESTART" = "3" ] && ok "cycle_restart_from_sequence = 3" || fail "cycle_restart_from_sequence = ${CYCLE_RESTART} (expected 3)"

info "Verifying PhaseEntries (is_recurring, watering_schedule_override)..."
ENTRIES_CHECK=$(get "${API}/nutrient-plans/${PLAN_KEY}/entries")
ENTRY_COUNT=$(echo "$ENTRIES_CHECK" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))")
[ "$ENTRY_COUNT" -eq 4 ] && ok "PhaseEntries: ${ENTRY_COUNT} found" || fail "PhaseEntries: ${ENTRY_COUNT} (expected 4)"

# Check is_recurring on VEGETATIVE entry
VEG_RECURRING=$(echo "$ENTRIES_CHECK" | python3 -c "
import sys, json
entries = json.load(sys.stdin)
veg = [e for e in entries if e['phase_name'] == 'vegetative']
print(veg[0]['is_recurring'] if veg else 'NOT_FOUND')
")
[ "$VEG_RECURRING" = "True" ] && ok "VEGETATIVE is_recurring = True" || fail "VEGETATIVE is_recurring = ${VEG_RECURRING}"

# Check watering_schedule_override on DORMANCY entry
DORM_OVERRIDE=$(echo "$ENTRIES_CHECK" | python3 -c "
import sys, json
entries = json.load(sys.stdin)
dorm = [e for e in entries if e['phase_name'] == 'dormancy']
override = dorm[0].get('watering_schedule_override') if dorm else None
print(override.get('interval_days') if override else 'NONE')
")
[ "$DORM_OVERRIDE" = "12" ] && ok "DORMANCY watering_schedule_override.interval_days = 12" || fail "DORMANCY override = ${DORM_OVERRIDE}"

# Validate plan
info "Validating NutrientPlan..."
VALID_RESP=$(get "${API}/nutrient-plans/${PLAN_KEY}/validate")
VALID=$(echo "$VALID_RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('valid', False))")
if [ "$VALID" = "True" ]; then
  ok "Plan validation: VALID"
else
  warn "Plan validation returned valid=${VALID} (may be expected for template without full EC coverage)"
  echo "$VALID_RESP" | python3 -m json.tool 2>/dev/null || echo "$VALID_RESP"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Summary"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo -e "  ${GREEN}BotanicalFamily:${NC}  Araceae                    (${FAMILY_KEY})"
echo -e "  ${GREEN}Species:${NC}          Monstera deliciosa          (${SPECIES_KEY})"
echo -e "  ${GREEN}LifecycleConfig:${NC}  perennial/day_neutral       (${LIFECYCLE_KEY})"
echo -e "  ${GREEN}Cultivars:${NC}        Thai Constellation          (${CV1_KEY})"
echo -e "                    Albo Variegata              (${CV2_KEY})"
echo -e "                    Borsigiana                  (${CV3_KEY})"
echo -e "  ${GREEN}Pest:${NC}             Schildlaeuse                (${PEST_SCALE_KEY})"
echo -e "  ${GREEN}Diseases:${NC}         Blattfleckenkrankheit       (${DIS_LEAFSPOT_KEY})"
echo -e "                    Russtaupilze                (${DIS_SOOTYMOLD_KEY})"
echo -e "  ${GREEN}Treatments:${NC}       Schmierseife                (${TRT_SOAP_KEY})"
echo -e "                    Alkohol-Abwischen           (${TRT_ALCOHOL_KEY})"
echo -e "                    Blaetter abbrausen          (${TRT_SHOWER_KEY})"
echo -e "                    Amblyseius cucumeris        (${TRT_AMBLY_KEY})"
echo -e "                    Cryptolaemus montrouzieri   (${TRT_CRYPTO_KEY})"
echo -e "                    Chrysoperla carnea          (${TRT_CHRYSO_KEY})"
echo -e "                    Steinernema feltiae         (${TRT_NEMATODE_KEY})"
echo -e "  ${GREEN}Fertilizer:${NC}       Gardol Gruenpflanzenduenger (${FERT_KEY})"
echo -e "  ${GREEN}NutrientPlan:${NC}     Monstera — Gardol           (${PLAN_KEY})"
echo -e "  ${GREEN}PhaseEntries:${NC}     GERMINATION                 (${PE1_KEY})"
echo -e "                    SEEDLING                    (${PE2_KEY})"
echo -e "                    VEGETATIVE                  (${PE3_KEY})"
echo -e "                    DORMANCY                    (${PE4_KEY})"
echo ""
echo -e "  ${YELLOW}Not imported (no REST endpoint):${NC}"
echo "    - IPM edges (susceptible_to, treated_by, targets)"
echo "    - Growth phases + requirement/nutrient profiles"
echo "    - CareProfile (auto-created per plant instance)"
echo ""
echo -e "${GREEN}Import complete.${NC}"
