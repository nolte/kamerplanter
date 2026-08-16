/**
 * Axe pass for the form dialogs (#1094).
 *
 * A dialog is the surface where accessibility fails hardest and most invisibly:
 * it takes over the page, so a missing `aria-modal`, an unlabelled title or a
 * control with no accessible name leaves a keyboard or screen-reader user with
 * no way out of a form a mouse user simply closes. None of that shows up in a
 * scan of the page *behind* it — the page tests mount these dialogs closed, so
 * they contribute nothing there.
 *
 * Scanned open, therefore, and scanned as the components they are rather than
 * through a page that happens to host them: driving a list page's toolbar to get
 * the dialog on screen would make the test fail for reasons that have nothing to
 * do with accessibility the moment that toolbar is rearranged.
 *
 * `document.body` is the container, not the render result. MUI renders a dialog
 * into a portal, so the fragment returned by `render` is empty and a scan of it
 * would pass while looking at nothing at all. The `minElements` floor is what
 * turns that mistake into a failure rather than a green run.
 */

import i18n from 'i18next';
import { describe, it, beforeEach } from 'vitest';

import PlantInstanceCreateDialog from '@/pages/pflanzen/PlantInstanceCreateDialog';

import { renderWithProviders } from '../helpers';
import { expectNoA11yViolations } from './expectNoA11yViolations';

/**
 * A dialog that failed to open still leaves MUI's portal root and a backdrop in
 * the body. This floor is what makes the assertion below mean "the open dialog
 * is accessible" rather than "a portal exists".
 */
const DIALOG_MIN_ELEMENTS = 25;

describe('Accessibility — form dialogs', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('PlantInstanceCreateDialog has no critical a11y violations when open', async () => {
    renderWithProviders(
      <PlantInstanceCreateDialog open onClose={() => {}} onCreated={() => {}} />,
    );

    await expectNoA11yViolations(document.body, { minElements: DIALOG_MIN_ELEMENTS });
  });
});
