import { cleanup, render, screen } from '@testing-library/react';
import { describe, it, expect, afterEach, beforeEach } from 'vitest';
import i18n from 'i18next';
import { I18nextProvider } from 'react-i18next';
import TaskOriginBadge from '@/components/common/TaskOriginBadge';

function renderBadge(origin: 'user' | 'system' | 'pipeline' | null | undefined) {
  return render(
    <I18nextProvider i18n={i18n}>
      <TaskOriginBadge origin={origin} />
    </I18nextProvider>,
  );
}

describe('TaskOriginBadge (REQ-006 FreeStyle, #1082)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });
  afterEach(cleanup);

  it('renders nothing for a user-authored task', () => {
    renderBadge('user');
    expect(screen.queryByTestId('task-origin-badge-user')).not.toBeInTheDocument();
    expect(screen.queryByTestId('task-origin-badge-pipeline')).not.toBeInTheDocument();
  });

  it('renders nothing when origin is absent', () => {
    renderBadge(null);
    expect(screen.queryByText(/Manuell|Pipeline|System/)).not.toBeInTheDocument();
  });

  it('marks a pipeline task as machine-generated with the localised label', () => {
    renderBadge('pipeline');
    const badge = screen.getByTestId('task-origin-badge-pipeline');
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveTextContent('Analyse-Pipeline');
  });

  it('marks a system task', () => {
    renderBadge('system');
    expect(screen.getByTestId('task-origin-badge-system')).toHaveTextContent('System');
  });
});
