/**
 * #3065 — a dialog's scrolling content keeps its width whether or not its
 * scrollbar is shown.
 *
 * With a classic, space-taking scrollbar (desktop Chrome on Linux/Windows) the
 * content of a `DialogContent` lost 15 px the moment it started to overflow,
 * which re-wrapped helper texts and toggle rows and moved every control below
 * them — the nightly measured it on the plant-create and the care-profile
 * dialogs. jsdom draws no scrollbar, so what is pinned here is the rule that
 * reserves the gutter, on the rendered element and in every theme the app can
 * select.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import Dialog from '@mui/material/Dialog';
import DialogContent from '@mui/material/DialogContent';
import { ThemeProvider, type Theme } from '@mui/material/styles';
import {
  darkTheme,
  highContrastTheme,
  kioskDarkTheme,
  kioskHighContrastTheme,
  kioskLightTheme,
  lightTheme,
} from '@/theme/theme';
import type { PlantPhoto } from '@/api/endpoints/plantPhotos';
import PlantPhotoLightbox from '@/pages/pflanzen/photos/PlantPhotoLightbox';

// The lightbox loads its image through an authenticated fetch; not under test.
vi.mock('@/components/common/AuthImage', () => ({ default: () => null }));

const THEMES: [string, Theme][] = [
  ['light', lightTheme],
  ['dark', darkTheme],
  ['high contrast', highContrastTheme],
  ['kiosk light', kioskLightTheme],
  ['kiosk dark', kioskDarkTheme],
  ['kiosk high contrast', kioskHighContrastTheme],
];

describe('DialogContent reserves its scrollbar gutter (#3065)', () => {
  it.each(THEMES)('in the %s theme', (_name, theme) => {
    render(
      <ThemeProvider theme={theme}>
        <Dialog open>
          <DialogContent data-testid="content">content</DialogContent>
        </Dialog>
      </ThemeProvider>,
    );
    const content = screen.getByTestId('content');
    expect(window.getComputedStyle(content).getPropertyValue('scrollbar-gutter')).toBe('stable');
  });
});

describe('the photo lightbox opts out of the gutter (#3065)', () => {
  it('keeps its edge-to-edge stage, so the close button sits in the corner', () => {
    const photo = { key: 'ph-1', uri: '/p.jpg', created_at: '2024-06-01T00:00:00Z' } as unknown as PlantPhoto;
    render(
      <ThemeProvider theme={lightTheme}>
        <PlantPhotoLightbox photo={photo} onClose={() => {}} />
      </ThemeProvider>,
    );
    const stage = screen.getByTestId('plant-photo-lightbox-close').closest('.MuiDialogContent-root');
    expect(stage).not.toBeNull();
    expect(window.getComputedStyle(stage as Element).getPropertyValue('scrollbar-gutter')).toBe('auto');
  });
});
