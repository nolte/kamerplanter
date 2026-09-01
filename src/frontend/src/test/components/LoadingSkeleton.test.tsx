import { render, screen, within } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import i18n from 'i18next';
import LoadingSkeleton from '@/components/common/LoadingSkeleton';

/**
 * #1324. The previous version of this file asserted
 * `container.querySelector('[aria-label="Loading table"]')` — i.e. exactly the
 * property the broken markup satisfied. `aria-label` sat on a `<div>`, which
 * maps to `generic`, ARIA prohibits naming a generic element, and the name was
 * dropped: the attribute was present in the DOM and absent from the
 * accessibility tree, so the old test stayed green while no screen-reader user
 * ever heard anything.
 *
 * These assertions go through the accessible role and name instead, which is
 * what assistive technology actually consumes. Verified in both directions:
 * with the old markup restored, they fail.
 */
describe('LoadingSkeleton', () => {
  const variants = ['table', 'form', 'card'] as const;

  it('resolves the loading wording, so the name assertions below are not vacuous', () => {
    expect(i18n.t('common.loading')).not.toBe('common.loading');
  });

  describe.each(variants)('%s variant', (variant) => {
    it('exposes a named status region instead of a name on a generic element', () => {
      render(<LoadingSkeleton variant={variant} />);
      expect(screen.getByRole('status')).toHaveAccessibleName(i18n.t('common.loading'));
    });

    it('gives the status region announceable text content', () => {
      // A live region announces its *content*, not its name. A `role="status"`
      // whose only children are decorative `<Skeleton>`s has nothing to say.
      render(<LoadingSkeleton variant={variant} />);
      expect(screen.getByRole('status')).toHaveTextContent(i18n.t('common.loading'));
    });

    it('leaves no aria-label on the busy wrapper', () => {
      const { container } = render(<LoadingSkeleton variant={variant} />);
      const wrapper = container.querySelector('[data-testid="loading-skeleton"]')!;
      expect(wrapper).not.toHaveAttribute('aria-label');
      expect(wrapper).toHaveAttribute('aria-busy', 'true');
    });

    it('keeps aria-busy off the live region itself', () => {
      // Measured in Chrome: an element carrying both reports busy=1 on the live
      // region, and `aria-busy` invites AT to defer presenting that region until
      // the updates finish — which, for a placeholder that is removed rather
      // than un-busied, never happens. The busy marker belongs on the wrapper,
      // the announcement on a node that is not itself busy.
      const { container } = render(<LoadingSkeleton variant={variant} />);
      const wrapper = container.querySelector('[data-testid="loading-skeleton"]') as HTMLElement;
      expect(within(wrapper).getByRole('status')).not.toHaveAttribute('aria-busy');
    });

    it('renders exactly one status region per skeleton', () => {
      const { container } = render(<LoadingSkeleton variant={variant} />);
      expect(container.querySelectorAll('[role="status"]')).toHaveLength(1);
    });
  });

  it('renders the specified number of rows for the table variant', () => {
    const { container } = render(<LoadingSkeleton variant="table" rows={3} />);
    // Title skeleton + header skeleton + 3 row skeletons
    const skeletons = container.querySelectorAll('.MuiSkeleton-root');
    expect(skeletons.length).toBeGreaterThanOrEqual(3);
  });

  it('defaults to the table variant', () => {
    const { container } = render(<LoadingSkeleton />);
    expect(container.querySelector('[data-testid="loading-skeleton"]')).toBeTruthy();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });
});
