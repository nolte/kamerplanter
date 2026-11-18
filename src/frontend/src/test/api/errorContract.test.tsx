import { act, render, renderHook, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { SnackbarProvider } from 'notistack';
import type { ReactNode } from 'react';
import { ApiError, parseApiError } from '@/api/errors';
import ErrorDisplay from '@/components/common/ErrorDisplay';
import { useApiError } from '@/hooks/useApiError';
import i18n from '@/i18n/i18n';
import speciesReducer, { fetchSpeciesList } from '@/store/slices/speciesSlice';
import pestDetectionReducer, { detectPests } from '@/store/slices/pestDetectionSlice';
import { configureStore } from '@reduxjs/toolkit';
import { http, HttpResponse } from 'msw';
import { server } from '@/test/mocks/server';

/**
 * #3013 (FRONTEND.md §10.3): the backend envelope's `error_code` is the contract,
 * its `message` is English (NFR-003). An envelope `{error_code: 'X', message: 'English'}`
 * must never put "English" into the German UI — not through `parseApiError`, not
 * through a slice's stored error, not through the toast of `useApiError`.
 */
const ENGLISH = 'English backend sentence that must never be rendered';

function envelope(errorCode: string, status = 500): ApiError {
  return new ApiError(
    {
      error_id: 'err_1',
      error_code: errorCode,
      message: ENGLISH,
      details: [{ field: 'body.name', reason: ENGLISH, code: 'value_error' }],
      timestamp: '',
      path: '/api/v1/x',
      method: 'GET',
    },
    status,
  );
}

describe('error contract (#3013)', () => {
  let previousLanguage: string;
  beforeEach(async () => {
    previousLanguage = i18n.language;
    await i18n.changeLanguage('de');
  });
  afterEach(async () => {
    await i18n.changeLanguage(previousLanguage);
  });

  it('parseApiError resolves an unknown code to the translated generic text, never the message', () => {
    const text = parseApiError(envelope('X'), i18n.t.bind(i18n));
    expect(text).not.toContain(ENGLISH);
    // 500 without a translated code: the status decides.
    expect(text).toBe(i18n.t('errors.server'));
  });

  it('parseApiError resolves a code with its own translation under errors.<code>', () => {
    expect(parseApiError(envelope('ACCOUNT_LOCKED', 423), i18n.t.bind(i18n))).toBe(
      i18n.t('errors.ACCOUNT_LOCKED'),
    );
  });

  it('a list slice stores an i18n key carried by the serialized error code, not the message', () => {
    const action = fetchSpeciesList.rejected(envelope('ENTITY_NOT_FOUND', 404), 'req-1', undefined as never);
    const state = speciesReducer(undefined, action);
    expect(state.error).toBe('errors.notFound');

    render(<ErrorDisplay error={state.error ?? ''} />);
    expect(screen.getByTestId('error-message').textContent).toBe(i18n.t('errors.notFound'));
    expect(screen.queryByText(ENGLISH)).toBeNull();
  });

  it('an unknown code in a slice falls back to the slice key, rendered in German', () => {
    const action = fetchSpeciesList.rejected(envelope('X'), 'req-2', undefined as never);
    const state = speciesReducer(undefined, action);
    render(<ErrorDisplay error={state.error ?? ''} />);
    const shown = screen.getByTestId('error-message').textContent ?? '';
    expect(shown).not.toContain(ENGLISH);
    expect(shown).toBe(i18n.t('errors.loadFailed'));
  });

  it('a thunk with its own reject value stores a key, not the backend message', async () => {
    server.use(
      http.post('/api/v1/t/:tenant/pests/plants/:plantKey/detect', () =>
        HttpResponse.json(
          { error_id: 'e', error_code: 'X', message: ENGLISH, details: [], timestamp: '', path: '', method: 'POST' },
          { status: 502 },
        ),
      ),
    );
    const store = configureStore({ reducer: { pestDetection: pestDetectionReducer } });
    await store.dispatch(detectPests({ plantKey: 'p1', image: new File(['x'], 'x.jpg', { type: 'image/jpeg' }) }));
    const stored = store.getState().pestDetection.error ?? '';
    expect(stored).toBe('errors.server');
    render(<ErrorDisplay error={stored} />);
    expect(screen.getByTestId('error-message').textContent).toBe(i18n.t('errors.server'));
    expect(screen.queryByText(ENGLISH)).toBeNull();
  });

  it('ErrorDisplay shows the generic text for a key the bundle does not know', () => {
    render(<ErrorDisplay error="errors.someCodeWithoutTranslation" />);
    expect(screen.getByTestId('error-message').textContent).toBe(i18n.t('errors.generic'));
  });

  it('useApiError toasts the translated text for an unknown code, not the message', async () => {
    const wrapper = ({ children }: { children: ReactNode }) => <SnackbarProvider>{children}</SnackbarProvider>;
    const { result } = renderHook(() => useApiError(), { wrapper });
    act(() => result.current.handleError(envelope('X', 418)));
    // No status mapping for 418 and no code translation: the generic fallback.
    expect(await screen.findByText(i18n.t('errors.unknown'))).toBeTruthy();
    expect(screen.queryByText(ENGLISH)).toBeNull();
  });
});
