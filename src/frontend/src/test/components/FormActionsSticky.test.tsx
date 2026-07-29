import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ThemeContextProvider } from '@/theme';
import '@/i18n';

// Force the compact breakpoint: below `sm` every dialog in this app renders
// `fullScreen`, which is exactly the case the pinned action row exists for.
vi.mock('@mui/material/useMediaQuery', () => ({ default: () => true }));

// Import after the mock so it is picked up.
import FormActions from '@/components/form/FormActions';

describe('FormActions — compact viewport', () => {
  it('pins the action row to the bottom of its scroll container', () => {
    render(
      <ThemeContextProvider>
        <FormActions onCancel={vi.fn()} />
      </ThemeContextProvider>,
    );

    const actions = screen.getByTestId('form-actions');
    const style = window.getComputedStyle(actions);

    // Without this the row is the last child of a scrolling `DialogContent`,
    // so on a long form the primary action sits far below the fold.
    expect(style.position).toBe('sticky');
    expect(style.bottom).toBe('0px');
  });

  it('keeps both actions operable while pinned', () => {
    render(
      <ThemeContextProvider>
        <FormActions onCancel={vi.fn()} />
      </ThemeContextProvider>,
    );

    expect(screen.getByTestId('form-submit-button')).toBeEnabled();
    expect(screen.getByTestId('form-cancel-button')).toBeEnabled();
  });
});
