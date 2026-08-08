import { renderHook } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import i18n from 'i18next';
import { useFieldViolations } from '@/hooks/useFieldViolations';
import type { FieldViolation } from '@/api/errors';
import '@/i18n';

const MESSAGE_KEYS = {
  WINTER_PATH_VIOLATION: 'pages.overwintering.errors.winterPathViolation',
} as const;

const FIELD_MAP = { slot_keys: 'slot_keys_input' } as const;

function violation(over: Partial<FieldViolation> = {}): FieldViolation {
  return { field: 'winter_action', reason: 'English reason', code: 'WINTER_PATH_VIOLATION', ...over };
}

describe('useFieldViolations', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('renders the translated message on the named field for a mapped code', () => {
    const setError = vi.fn();
    const { result } = renderHook(() =>
      useFieldViolations(setError, { messageKeys: MESSAGE_KEYS }),
    );
    const handled = result.current(violation());
    expect(handled).toBe(true);
    expect(setError).toHaveBeenCalledWith('winter_action', {
      type: 'WINTER_PATH_VIOLATION',
      message: i18n.t('pages.overwintering.errors.winterPathViolation'),
    });
    // The German message is used — never the backend's English reason.
    const [, arg] = setError.mock.calls[0];
    expect(arg.message).not.toBe('English reason');
  });

  it('skips an unmapped code and leaves the field untouched', () => {
    const setError = vi.fn();
    const { result } = renderHook(() =>
      useFieldViolations(setError, { messageKeys: MESSAGE_KEYS }),
    );
    const handled = result.current(violation({ code: 'SOME_NEW_RULE' }));
    expect(handled).toBe(false);
    expect(setError).not.toHaveBeenCalled();
  });

  it('remaps the server field name onto the form field name', () => {
    const setError = vi.fn();
    const { result } = renderHook(() =>
      useFieldViolations(setError, {
        messageKeys: { watering_target_required: 'pages.wateringLogs.errors.targetRequired' },
        fieldMap: FIELD_MAP,
      }),
    );
    result.current(violation({ field: 'slot_keys', code: 'watering_target_required' }));
    expect(setError).toHaveBeenCalledWith('slot_keys_input', expect.objectContaining({
      type: 'watering_target_required',
    }));
  });
});
