import { act, renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, afterEach, beforeEach } from 'vitest';
import { http, HttpResponse } from 'msw';
import i18n from 'i18next';
import { useRequestLanguage } from '@/hooks/useRequestLanguage';
import { useSuccessionRecommendation } from '@/features/gardenPlanner/history/useSuccessionRecommendation';
import { bedSheetEntry, type CacheScope } from '@/features/gardenPlanner/offline/planCache';
import { server } from '../mocks/server';

/**
 * #2902 — answers the server words in the UI language are loaded again after a language
 * switch, and a cache that keeps such an answer keeps it per language.
 */
describe('useRequestLanguage', () => {
  afterEach(async () => {
    await act(async () => {
      await i18n.changeLanguage('de');
    });
  });

  it('is the primary subtag of the UI language and follows a switch', async () => {
    await act(async () => {
      await i18n.changeLanguage('de');
    });
    const { result } = renderHook(() => useRequestLanguage());
    expect(result.current).toBe('de');

    await act(async () => {
      await i18n.changeLanguage('en-GB');
    });
    expect(result.current).toBe('en');
  });
});

describe('a server-worded answer is loaded again on a language switch', () => {
  let languages: string[] = [];

  beforeEach(async () => {
    languages = [];
    await act(async () => {
      await i18n.changeLanguage('de');
    });
    server.use(
      http.get('/api/v1/t/:tenant/locations/:key/succession-recommendation', ({ request }) => {
        const language = request.headers.get('Accept-Language') ?? '<none>';
        languages.push(language);
        return HttpResponse.json({
          location_key: 'bed',
          rotation_applicable: true,
          not_applicable_reason: null,
          status: 'ok',
          previous: null,
          target: 'medium_feeder',
          families: [
            {
              family_key: 'brassica',
              family_name: 'Brassicaceae',
              benefit_score: 0.8,
              benefit_reason: null,
              pause_years: 4,
              species: [
                {
                  species_key: 'cabbage',
                  scientific_name: 'Brassica oleracea',
                  common_name: language === 'en' ? 'Cabbage' : 'Weißkohl',
                  nutrient_demand: 'medium_feeder',
                  nitrogen_fixing: false,
                },
              ],
            },
          ],
          held_back: [],
          fallow_option: false,
        });
      }),
    );
  });

  afterEach(async () => {
    await act(async () => {
      await i18n.changeLanguage('de');
    });
  });

  it('reads the succession recommendation again, in the new language', async () => {
    const { result } = renderHook(() => useSuccessionRecommendation('bed', 0));
    const commonName = () =>
      result.current.state.status === 'ready'
        ? result.current.state.recommendation.families[0].species[0].common_name
        : null;
    await waitFor(() => expect(commonName()).toBe('Weißkohl'));

    await act(async () => {
      await i18n.changeLanguage('en');
    });

    await waitFor(() => expect(commonName()).toBe('Cabbage'));
    expect(languages).toEqual(['de', 'en']);
  });
});

describe('bed-sheet offline cache', () => {
  const scope: CacheScope = { userKey: 'u1', tenantKey: 't1' };

  it('keys the bed sheet by language, so offline never shows the names of another language', () => {
    const german = bedSheetEntry(scope, 'bed', 'de');
    const english = bedSheetEntry(scope, 'bed', 'en');

    expect(german.key).not.toBe(english.key);
    expect(english.key.endsWith('#lang=en')).toBe(true);
    expect(german.table).toBe('bedSheets');
  });
});
