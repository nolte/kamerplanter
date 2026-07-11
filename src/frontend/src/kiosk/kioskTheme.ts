import type { ThemeOptions } from '@mui/material/styles';

/**
 * UI-NFR-019 §2.2 — kiosk touch-target overrides, layered on top of the base
 * (usually high-contrast) theme via ``createTheme(base, kioskThemeOverrides)``.
 *
 * Enforces the greenhouse touch dimensions: interactive elements ≥ 64×64px
 * (R-007), MUI component defaults ``size: 'large'`` (R-013), list rows ≥ 64px
 * (R-010), action icons enlarged (R-012). Primary 72px actions (R-008) are set
 * per-element on the kiosk start-page tiles / overlay buttons.
 */

/** Minimum touch-target edge for any interactive element in kiosk mode (R-007). */
export const KIOSK_TOUCH_TARGET = 64;
/** Recommended edge for primary actions (Save/Confirm/Scan) in kiosk mode (R-008). */
export const KIOSK_PRIMARY_TOUCH_TARGET = 72;

export const kioskThemeOverrides: ThemeOptions = {
  components: {
    MuiButton: {
      defaultProps: {
        size: 'large',
      },
      styleOverrides: {
        root: {
          minHeight: KIOSK_TOUCH_TARGET,
          minWidth: KIOSK_TOUCH_TARGET,
          fontSize: '1.125rem',
          paddingInline: 24,
        },
      },
    },
    MuiIconButton: {
      defaultProps: {
        size: 'large',
      },
      styleOverrides: {
        root: {
          minWidth: KIOSK_TOUCH_TARGET,
          minHeight: KIOSK_TOUCH_TARGET,
        },
      },
    },
    MuiFab: {
      styleOverrides: {
        root: {
          minWidth: KIOSK_PRIMARY_TOUCH_TARGET,
          minHeight: KIOSK_PRIMARY_TOUCH_TARGET,
        },
      },
    },
    MuiTextField: {
      defaultProps: {
        size: 'medium',
      },
    },
    MuiSelect: {
      defaultProps: {
        size: 'medium',
      },
    },
    MuiCheckbox: {
      defaultProps: {
        size: 'medium',
      },
      styleOverrides: {
        // R-011 — the touch area is ≥ 64×64px regardless of the glyph size.
        root: {
          padding: 20,
        },
      },
    },
    MuiRadio: {
      styleOverrides: {
        root: {
          padding: 20,
        },
      },
    },
    MuiSwitch: {
      defaultProps: {
        size: 'medium',
      },
    },
    MuiListItemButton: {
      styleOverrides: {
        root: {
          minHeight: KIOSK_TOUCH_TARGET,
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          minHeight: KIOSK_TOUCH_TARGET,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        // R-010 — kiosk list rows ≥ 64px tall.
        root: {
          paddingTop: 16,
          paddingBottom: 16,
        },
      },
    },
    MuiSvgIcon: {
      styleOverrides: {
        // R-012 — icons ≥ 32px in kiosk mode.
        root: {
          fontSize: '2rem',
        },
      },
    },
  },
};
