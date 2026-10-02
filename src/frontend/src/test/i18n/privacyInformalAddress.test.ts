import { describe, it, expect } from 'vitest';

/**
 * #1845 / #1894 — the UI addresses the user with "du" (DOCS.md voice). The
 * privacy page (#1845) and then the whole German locale (#1894) were converted
 * from the formal "Sie/Ihr"; this guard keeps the whole DE catalogue that way.
 *
 * A sentence-initial or mid-sentence "Sie" / "Ihr" can also be the third person
 * ("Sie sehen im Winter schlafend aus" about plants, "Ihr Einsatz" about
 * beneficials). Those are the ALLOWED entries below — each one names the key it
 * lives at and the reason. The list is exact (file + key path), so a new formal
 * string anywhere else fails with its key path, and a stale entry fails too.
 *
 * Spellings this does not see: a formal imperative without a pronoun ("Bitte
 * bestätigen" is neutral German and allowed), a formal verb form in a sentence
 * whose pronoun lives in another key, strings assembled from parts in code, and
 * German defaults passed to `t(key, 'default')` in TSX (those are not in the
 * catalogue).
 */
const FORMAL = /\b(Sie|Ihnen|Ihr|Ihre|Ihren|Ihrem|Ihrer|Ihres)\b/;

// Read the raw files, not the imported JSON modules: the i18n bootstrap merges
// the catalogue files into one shared object, which would re-key every string
// under "core.json". Globbing means a German catalogue file added later is scanned too; the file-list assertion below makes that addition a deliberate edit.
const RAW = import.meta.glob('@/i18n/locales/de/*.json', {
  eager: true,
  query: '?raw',
  import: 'default',
}) as Record<string, string>;

const CATALOGUES: Record<string, unknown> = Object.fromEntries(
  Object.entries(RAW).map(([file, raw]) => [file.split('/').pop() as string, JSON.parse(raw)]),
);

/** `file:key.path` -> reason the string is third person, not an address. */
const THIRD_PERSON_ALLOWLIST: Record<string, string> = {
  'core.json:storageSettings.credentialsSectionDesc': '"Sie" = the S3 keys (plural), not the reader',
  'glossary.json:glossary.nuetzlinge.long': '"Ihr gezielter Einsatz" = the beneficial insects',
  'glossary.json:glossary.dormancy.long': '"Sie überdauert" = the plant',
  'glossary.json:glossary.dormancy.beginnerTip': '"Sie sehen … aus" = the plants',
  'pages.json:pages.season.phaseHelp.winter_dormancy': '"Sie werden … gegossen" = the plants',
  'pages.json:pages.siteDetail.climate.empty': '"Sie werden … abgerufen" = the climate normals',
  'pages.json:pages.substrates.additivesHelper': '"Sie werden … dosiert" = the additives',
  'pages.json:pages.plantPhotos.referenceIntro': '"Sie zeigen die Art" = the reference images',
  'pages.json:pages.phaseSequences.definitionsIntro': '"Sie können … wiederverwendet werden" = the phases',
  'pages.json:pages.pestDetail.sectionBeneficialsIntro2': '"Ihr Einsatz" = the beneficial insects',
  'pages.json:pages.harvest.completeHarvestAlreadyDone': '"Ihr Lebenszyklus" = the plant',
  'pages.json:pages.plantDiary.environment.sectionHint': '"Sie werden getrennt gespeichert" = the sensor values',
  'pages.json:pages.plantDiary.analysis.waiting': '"Sie läuft" = the analysis',
  'pages.json:pages.tasks.cannotDeleteReopened': '"Sie trägt … lässt sich" = the reopened task',
  'pages.json:pages.diaryOverview.description': '"Sie läuft" = the analysis',
};

function strings(node: unknown, path: string): Array<[string, string]> {
  if (typeof node === 'string') return [[path, node]];
  if (Array.isArray(node)) return node.flatMap((value, i) => strings(value, `${path}[${i}]`));
  if (node && typeof node === 'object') {
    return Object.entries(node as Record<string, unknown>).flatMap(([key, value]) =>
      strings(value, path ? `${path}.${key}` : key),
    );
  }
  return [];
}

const all: Array<[string, string]> = Object.entries(CATALOGUES).flatMap(([file, node]) =>
  strings(node, '').map(([path, text]): [string, string] => [`${file}:${path}`, text]),
);

describe('German locale — informal address', () => {
  it('reads every catalogue file', () => {
    expect(Object.keys(CATALOGUES).sort()).toEqual(['core.json', 'enums.json', 'glossary.json', 'pages.json']);
    expect(all.length).toBeGreaterThan(2000);
  });

  it('uses du, never the formal Sie/Ihr (except reasoned third-person uses)', () => {
    const formal = all
      .filter(([key, text]) => FORMAL.test(text) && !(key in THIRD_PERSON_ALLOWLIST))
      .map(([key, text]) => `${key}: ${text}`);
    expect(formal).toEqual([]);
  });

  it('keeps no stale allow-list entry (each must still be a formal-pattern hit)', () => {
    const byKey = new Map(all);
    const stale = Object.keys(THIRD_PERSON_ALLOWLIST).filter((key) => {
      const text = byKey.get(key);
      return text === undefined || !FORMAL.test(text);
    });
    expect(stale).toEqual([]);
  });

  it('the detector sees each formal form and passes the informal one', () => {
    for (const text of ['Sie haben', 'über Sie', 'Ihren Status', 'Ihr Konto', 'wenden Sie sich', 'Ihnen']) {
      expect(FORMAL.test(text)).toBe(true);
    }
    for (const text of ['Du hast', 'dein Konto', 'wende dich', 'Bitte bestätigen']) {
      expect(FORMAL.test(text)).toBe(false);
    }
  });
});
