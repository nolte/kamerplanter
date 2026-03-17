import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import type { OnboardingState, StarterKit, Species, Site, ExperienceLevel, NutrientPlanMatch, PlantConfig } from '@/api/types';
import * as onboardingApi from '@/api/endpoints/onboarding';
import * as starterKitsApi from '@/api/endpoints/starterKits';
import * as speciesApi from '@/api/endpoints/species';
import * as sitesApi from '@/api/endpoints/sites';
import * as favoritesApi from '@/api/endpoints/favorites';

interface OnboardingSliceState {
  state: OnboardingState | null;
  kits: StarterKit[];
  loading: boolean;
  error: string | null;
  favoriteSpeciesKeys: string[];
  favoriteNutrientPlanKeys: string[];
  matchingNutrientPlans: NutrientPlanMatch[];
  matchingPlansLoading: boolean;
  allSpecies: Species[];
  allSpeciesLoading: boolean;
  existingFavoriteKeys: string[];
  existingSites: Site[];
  existingSitesLoading: boolean;
}

const initialState: OnboardingSliceState = {
  state: null,
  kits: [],
  loading: false,
  error: null,
  favoriteSpeciesKeys: [],
  favoriteNutrientPlanKeys: [],
  matchingNutrientPlans: [],
  matchingPlansLoading: false,
  allSpecies: [],
  allSpeciesLoading: false,
  existingFavoriteKeys: [],
  existingSites: [],
  existingSitesLoading: false,
};

export const fetchOnboardingState = createAsyncThunk(
  'onboarding/fetchState',
  async () => {
    return onboardingApi.getState();
  },
);

export const fetchStarterKits = createAsyncThunk(
  'onboarding/fetchKits',
  async (params?: { difficulty?: string; useTenant?: boolean }) => {
    if (params?.useTenant) {
      return starterKitsApi.listKitsForTenant(params.difficulty);
    }
    return starterKitsApi.listKits(params?.difficulty);
  },
);

export const fetchExistingSites = createAsyncThunk(
  'onboarding/fetchExistingSites',
  async () => {
    return sitesApi.listSites(0, 100);
  },
);

export const completeOnboarding = createAsyncThunk(
  'onboarding/complete',
  async (payload: {
    kit_id?: string;
    experience_level?: ExperienceLevel;
    site_name?: string;
    selected_site_key?: string;
    plant_count?: number;
    plant_configs?: PlantConfig[];
    has_ro_system?: boolean;
    tap_water_ec_ms?: number;
    tap_water_ph?: number;
    favorite_species_keys?: string[];
    favorite_nutrient_plan_keys?: string[];
    smart_home_enabled?: boolean;
  }) => {
    return onboardingApi.complete(payload);
  },
);

export const skipOnboarding = createAsyncThunk(
  'onboarding/skip',
  async () => {
    return onboardingApi.skip();
  },
);

export const resetOnboarding = createAsyncThunk(
  'onboarding/reset',
  async () => {
    return onboardingApi.reset();
  },
);

export const saveProgress = createAsyncThunk(
  'onboarding/saveProgress',
  async (payload: {
    wizard_step: number;
    selected_kit_id?: string;
    selected_experience_level?: ExperienceLevel;
    site_name?: string;
    site_type?: string;
    selected_site_key?: string;
    plant_count?: number;
    plant_configs?: PlantConfig[];
    favorite_species_keys?: string[];
    favorite_nutrient_plan_keys?: string[];
    smart_home_enabled?: boolean;
  }) => {
    return onboardingApi.updateProgress(payload);
  },
);

export const fetchMatchingNutrientPlans = createAsyncThunk(
  'onboarding/fetchMatchingPlans',
  async (params: { speciesKeys: string[] }) => {
    return favoritesApi.getMatchingNutrientPlans(params.speciesKeys);
  },
);

export const fetchAllSpecies = createAsyncThunk(
  'onboarding/fetchAllSpecies',
  async () => {
    const result = await speciesApi.listSpecies(0, 500);
    return result.items;
  },
);

export const fetchExistingFavorites = createAsyncThunk(
  'onboarding/fetchExistingFavorites',
  async () => {
    const entries = await favoritesApi.listFavorites('species');
    return entries.map((e) => e.target_key);
  },
);

const onboardingSlice = createSlice({
  name: 'onboarding',
  initialState,
  reducers: {
    clearError(state) {
      state.error = null;
    },
    setFavoriteSpecies(state, action: PayloadAction<string[]>) {
      state.favoriteSpeciesKeys = action.payload;
    },
    toggleFavoriteSpecies(state, action: PayloadAction<string>) {
      const key = action.payload;
      const idx = state.favoriteSpeciesKeys.indexOf(key);
      if (idx >= 0) {
        state.favoriteSpeciesKeys.splice(idx, 1);
      } else {
        state.favoriteSpeciesKeys.push(key);
      }
    },
    setFavoriteNutrientPlans(state, action: PayloadAction<string[]>) {
      state.favoriteNutrientPlanKeys = action.payload;
    },
    toggleFavoriteNutrientPlan(state, action: PayloadAction<string>) {
      const key = action.payload;
      const idx = state.favoriteNutrientPlanKeys.indexOf(key);
      if (idx >= 0) {
        state.favoriteNutrientPlanKeys.splice(idx, 1);
      } else {
        state.favoriteNutrientPlanKeys.push(key);
      }
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch state
      .addCase(fetchOnboardingState.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchOnboardingState.fulfilled, (state, action) => {
        state.loading = false;
        state.state = action.payload;
        // Restore favorites from saved state
        if (action.payload.favorite_species_keys?.length) {
          state.favoriteSpeciesKeys = action.payload.favorite_species_keys;
        }
        if (action.payload.favorite_nutrient_plan_keys?.length) {
          state.favoriteNutrientPlanKeys = action.payload.favorite_nutrient_plan_keys;
        }
      })
      .addCase(fetchOnboardingState.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load onboarding state';
      })
      // Fetch kits
      .addCase(fetchStarterKits.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchStarterKits.fulfilled, (state, action) => {
        state.loading = false;
        state.kits = action.payload;
      })
      .addCase(fetchStarterKits.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message ?? 'Failed to load starter kits';
      })
      // Complete
      .addCase(completeOnboarding.fulfilled, (state) => {
        if (state.state) {
          state.state.completed = true;
        }
      })
      // Skip
      .addCase(skipOnboarding.fulfilled, (state, action) => {
        state.state = action.payload;
      })
      // Reset
      .addCase(resetOnboarding.fulfilled, (state, action) => {
        state.state = action.payload;
        state.favoriteSpeciesKeys = [];
        state.favoriteNutrientPlanKeys = [];
        state.matchingNutrientPlans = [];
        state.existingSites = [];
      })
      // Save progress
      .addCase(saveProgress.fulfilled, (state, action) => {
        state.state = action.payload;
      })
      // Fetch matching nutrient plans
      .addCase(fetchMatchingNutrientPlans.pending, (state) => {
        state.matchingPlansLoading = true;
      })
      .addCase(fetchMatchingNutrientPlans.fulfilled, (state, action) => {
        state.matchingPlansLoading = false;
        state.matchingNutrientPlans = action.payload;
      })
      .addCase(fetchMatchingNutrientPlans.rejected, (state) => {
        state.matchingPlansLoading = false;
        state.matchingNutrientPlans = [];
      })
      // Fetch all species
      .addCase(fetchAllSpecies.pending, (state) => {
        state.allSpeciesLoading = true;
      })
      .addCase(fetchAllSpecies.fulfilled, (state, action) => {
        state.allSpeciesLoading = false;
        state.allSpecies = action.payload;
      })
      .addCase(fetchAllSpecies.rejected, (state) => {
        state.allSpeciesLoading = false;
      })
      // Fetch existing sites
      .addCase(fetchExistingSites.pending, (state) => {
        state.existingSitesLoading = true;
      })
      .addCase(fetchExistingSites.fulfilled, (state, action) => {
        state.existingSitesLoading = false;
        state.existingSites = action.payload;
      })
      .addCase(fetchExistingSites.rejected, (state) => {
        state.existingSitesLoading = false;
      })
      // Fetch existing favorites — merge into selection
      .addCase(fetchExistingFavorites.fulfilled, (state, action) => {
        state.existingFavoriteKeys = action.payload;
        // Merge existing backend favorites into the current selection
        const currentSet = new Set(state.favoriteSpeciesKeys);
        for (const key of action.payload) {
          if (!currentSet.has(key)) {
            state.favoriteSpeciesKeys.push(key);
          }
        }
      });
  },
});

export const {
  clearError,
  setFavoriteSpecies,
  toggleFavoriteSpecies,
  setFavoriteNutrientPlans,
  toggleFavoriteNutrientPlan,
} = onboardingSlice.actions;
export default onboardingSlice.reducer;
