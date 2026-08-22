import { describe, it, expect, beforeEach } from 'vitest';
import { screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import i18n from 'i18next';
import { renderWithProviders } from '@/test/helpers';
import type { DiaryAnalysis } from '@/api/types';
import DiaryAnalysisResult from '@/components/diary/DiaryAnalysisResult';

/**
 * REQ-051 §6.4 — how an analysis result is presented.
 *
 * Two acceptance criteria are checked here because both are stated as hard
 * requirements rather than layout preferences: AK-20 (the disclaimer is always
 * visible, never behind a disclosure) and AK-30 (confidence appears as a number
 * *and* in words).
 */

const DISCLAIMER =
  'Diese Einschätzung stammt von einem Sprachmodell, ist eine Hypothese und ersetzt keine fachliche Prüfung.';

function analysis(overrides: Partial<DiaryAnalysis> = {}): DiaryAnalysis {
  return {
    summary: 'Vermutlich Staunässe nach dem Umtopfen, kein Pilzbefall erkennbar.',
    findings: [
      {
        label: 'Staunässe / Wurzelstress',
        confidence: 0.72,
        rationale: 'Saurer Substratgeruch und hängende untere Blätter kurz nach dem Umtopfen.',
      },
    ],
    recommended_actions: ['Substrat abtrocknen lassen', 'Drainage prüfen'],
    analyzed_photo_ids: ['a1', 'a2'],
    model: 'claude-opus-5',
    recipe_version: '1.0.0',
    analyzed_at: '2026-08-04T07:14:52Z',
    disclaimer: DISCLAIMER,
    ...overrides,
  };
}

describe('DiaryAnalysisResult (REQ-051 §6.4)', () => {
  beforeEach(() => {
    i18n.changeLanguage('de');
  });

  it('shows the summary first and the disclaimer without any expansion (AK-20)', () => {
    renderWithProviders(<DiaryAnalysisResult analysis={analysis()} />);

    expect(screen.getByTestId('diary-analysis-summary')).toHaveTextContent(/Staunässe/);

    const disclaimer = screen.getByTestId('diary-analysis-disclaimer');
    expect(disclaimer).toBeVisible();
    expect(disclaimer).toHaveTextContent(DISCLAIMER);

    // AK-20 in its load-bearing form: the disclaimer must not sit inside the
    // collapsible finding list, where "present in the DOM" would be true while
    // the user still could not see it.
    const findings = screen.getByTestId('diary-analysis-findings');
    expect(findings).not.toContainElement(disclaimer);
  });

  it('keeps the disclaimer visible when there is no findings list at all (AK-20)', () => {
    renderWithProviders(<DiaryAnalysisResult analysis={analysis({ findings: [] })} />);

    expect(screen.queryByTestId('diary-analysis-findings')).not.toBeInTheDocument();
    expect(screen.getByTestId('diary-analysis-disclaimer')).toHaveTextContent(DISCLAIMER);
  });

  it('falls back to a disclaimer text when the stored one is empty (AK-20)', () => {
    renderWithProviders(<DiaryAnalysisResult analysis={analysis({ disclaimer: '' })} />);

    expect(screen.getByTestId('diary-analysis-disclaimer')).toHaveTextContent(
      /Sprachmodell/,
    );
  });

  it('renders each finding’s confidence as a number and in words (AK-30)', async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <DiaryAnalysisResult
        analysis={analysis({
          findings: [
            { label: 'Staunässe', confidence: 0.72, rationale: 'Substratgeruch.' },
            { label: 'Spinnmilben', confidence: 0.15, rationale: 'Keine Gespinste sichtbar.' },
          ],
        })}
      />,
    );

    await user.click(screen.getByTestId('diary-analysis-findings-toggle'));

    const chips = await screen.findAllByTestId('diary-analysis-confidence');
    expect(chips).toHaveLength(2);

    // The number alone would not satisfy AK-30 — a bare percentage claims a
    // precision a language model does not have.
    expect(chips[0]).toHaveTextContent('72');
    expect(chips[0]).toHaveTextContent('eher wahrscheinlich');
    expect(chips[1]).toHaveTextContent('15');
    expect(chips[1]).toHaveTextContent('sehr unsicher');
  });

  it('lists the recommended actions and the provenance', () => {
    renderWithProviders(<DiaryAnalysisResult analysis={analysis()} photoRefs={['a1', 'a2', 'a3']} />);

    const actions = screen.getByTestId('diary-analysis-actions');
    expect(within(actions).getByText('Substrat abtrocknen lassen')).toBeInTheDocument();
    expect(within(actions).getByText('Drainage prüfen')).toBeInTheDocument();

    const provenance = screen.getByTestId('diary-analysis-provenance');
    expect(provenance).toHaveTextContent('claude-opus-5');
    expect(provenance).toHaveTextContent('1.0.0');
    // Which photos actually went in — 2 of the entry's 3 (§2.5.3).
    expect(provenance).toHaveTextContent(/2 von 3/);
  });

  it('translates the whole result into English as well (AK-28)', async () => {
    await i18n.changeLanguage('en');
    renderWithProviders(<DiaryAnalysisResult analysis={analysis()} />);

    expect(screen.getByText('AI analysis result')).toBeInTheDocument();
    expect(screen.getByText('Recommended actions')).toBeInTheDocument();
    await i18n.changeLanguage('de');
  });
});
