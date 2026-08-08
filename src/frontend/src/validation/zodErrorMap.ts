import { z } from 'zod';
import i18n from 'i18next';

/**
 * A global zod error map that renders every built-in constraint message through
 * i18next, so a bare constraint (`z.number().gt(0)`, `z.string().min(1)`, …) can
 * never ship zod's English default into the German UI (#1016).
 *
 * ## Why a global map, not per-constraint messages
 *
 * The sweep found the class, not an instance: ~670 constraint calls and ~640
 * bare `z.number()` / `z.string()` across 72 schema files, the overwhelming
 * majority without an explicit message. Annotating each is both a large edit and
 * a standing trap — the next `z.number().min(0)` a developer writes would ship an
 * English default again. `z.config({ customError })` closes the class in one
 * place: it fires only when a constraint carries no inline message, so the
 * handful of schemas that already pass `z.string().min(1, t('…'))` keep winning.
 *
 * ## Language switching
 *
 * The map calls `i18n.t()` at validation time, so it always resolves in the
 * active language without re-registration on `languageChanged`.
 *
 * Keys live in the `validation.*` namespace of `core.json` (FRONTEND.md §3.3),
 * which is loaded synchronously for both locales, so a message is available even
 * before the feature bundles finish loading.
 */
const customError: z.core.$ZodErrorMap = (issue) => {
  const t = i18n.t.bind(i18n);

  switch (issue.code) {
    case 'invalid_type': {
      // A cleared field emits `null` (FormNumberField) or `undefined`; treat that
      // as "required" rather than "wrong type", which reads far better under a
      // required field than "expected number, received null".
      if (issue.input === null || issue.input === undefined) {
        return t('validation.required');
      }
      return t('validation.invalidType', { expected: issue.expected });
    }
    case 'too_small': {
      const minimum = Number(issue.minimum);
      if (issue.origin === 'number' || issue.origin === 'int' || issue.origin === 'bigint') {
        return issue.inclusive
          ? t('validation.numberMin', { minimum })
          : t('validation.numberGt', { minimum });
      }
      if (issue.origin === 'string') {
        return minimum <= 1
          ? t('validation.required')
          : t('validation.stringMin', { minimum });
      }
      return t('validation.arrayMin', { minimum });
    }
    case 'too_big': {
      const maximum = Number(issue.maximum);
      if (issue.origin === 'number' || issue.origin === 'int' || issue.origin === 'bigint') {
        return issue.inclusive
          ? t('validation.numberMax', { maximum })
          : t('validation.numberLt', { maximum });
      }
      if (issue.origin === 'string') {
        return t('validation.stringMax', { maximum });
      }
      return t('validation.arrayMax', { maximum });
    }
    case 'not_multiple_of':
      return t('validation.multipleOf', { divisor: Number(issue.divisor) });
    case 'invalid_format': {
      if (issue.format === 'email') return t('validation.email');
      if (issue.format === 'url') return t('validation.url');
      return t('validation.invalidFormat');
    }
    case 'invalid_value':
    case 'invalid_union':
      return t('validation.invalidOption');
    case 'unrecognized_keys':
      return t('validation.invalidFormat');
    default:
      // custom refinements carry their own message and never reach here; any
      // remaining code (invalid_key, invalid_element, a message-less custom
      // refine) falls back to a generic German sentence, never an English zod
      // default.
      return t('validation.invalid');
  }
};

/**
 * Register the global zod error map. Idempotent and side-effect free beyond the
 * one `z.config` call; invoked once from the i18n bootstrap so it is active in
 * both the app and the test environment (both import `@/i18n`).
 */
export function configureZodErrorMap(): void {
  z.config({ customError });
}
