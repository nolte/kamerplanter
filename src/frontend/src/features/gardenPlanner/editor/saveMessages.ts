/**
 * Plain-language text for a refused or failed save (REQ-053 GP-UX-017, UI-NFR-004): which object
 * and field a 422 finding belongs to, what the code means and what to do about it.
 */
import type { TFunction } from 'i18next';
import type { PlanFinding, PlanSaveFailure } from '../api/gardenPlan';
import type { PlanModel } from '../model/planModel';
import type { PlanOperation } from '../model/types';

const PREFIX = 'pages.gardenPlan.editor.save';

/** The name of the object an operation works on, or `null` when it names none (the garden outline). */
export function operationSubject(
  op: PlanOperation,
  plan: PlanModel,
  t: TFunction,
): string | null {
  switch (op.op) {
    case 'create_location':
      return op.data.name || t(`${PREFIX}.subject.bed`);
    case 'create_garden_object':
      return op.data.label || t(`${PREFIX}.subject.object`);
    case 'set_boundary':
      return t(`${PREFIX}.subject.boundary`);
    default: {
      const named =
        op.entity === 'location' ? plan.locations[op.key]?.name : plan.gardenObjects[op.key]?.label;
      return named || t(`${PREFIX}.subject.${op.entity === 'location' ? 'bed' : 'object'}`);
    }
  }
}

/** The text of a code this client knows (`''` otherwise); the geometry codes share the editor notices. */
export function knownCodeText(code: string, t: TFunction): string {
  if (!code) return '';
  const notice = t(`pages.gardenPlan.editor.notice.${code}`, { defaultValue: '' });
  if (typeof notice === 'string' && notice) return notice;
  const own = t(`${PREFIX}.code.${code}`, { defaultValue: '' });
  return typeof own === 'string' ? own : '';
}

/** What a finding's code means; a code that is not known is named, never swallowed. */
export function findingText(code: string, t: TFunction): string {
  return knownCodeText(code, t) || t(`${PREFIX}.code.unknown`, { code });
}

export interface FindingLine {
  /** Stable React key. */
  id: string;
  text: string;
}

/**
 * One line per finding: "Change 3 - Bed 2, field geometry: ...". `ops` are the operations that were
 * sent, as a snapshot - the findings index into exactly that list.
 */
export function findingLines(
  findings: readonly PlanFinding[],
  ops: readonly PlanOperation[],
  plan: PlanModel,
  t: TFunction,
): FindingLine[] {
  return findings.map((finding, index) => {
    const op = finding.opIndex === null ? undefined : ops[finding.opIndex];
    const subject = op ? operationSubject(op, plan, t) : null;
    const where =
      finding.opIndex === null
        ? ''
        : t(`${PREFIX}.finding.where`, {
            n: finding.opIndex + 1,
            subject: subject ?? t(`${PREFIX}.subject.boundary`),
          });
    const field = finding.field ? t(`${PREFIX}.finding.field`, { field: finding.field }) : '';
    return {
      id: `${finding.opIndex ?? 'x'}-${finding.field}-${finding.code}-${index}`,
      text: [where, field, findingText(finding.code, t)].filter(Boolean).join(' '),
    };
  });
}

/** The headline of a failure that is not a conflict. */
export function failureTitle(
  failure: Exclude<PlanSaveFailure, { kind: 'conflict' }>,
  t: TFunction,
): string {
  if (failure.kind === 'failed') return t(`${PREFIX}.failed.title`);
  if (failure.status === 403) return t(`${PREFIX}.forbidden.title`);
  if (failure.status === 404) return t(`${PREFIX}.gone.title`);
  return t(`${PREFIX}.rejected.title`);
}

/** What to do next. */
export function failureHint(
  failure: Exclude<PlanSaveFailure, { kind: 'conflict' }>,
  t: TFunction,
): string {
  if (failure.kind === 'failed') return t(`${PREFIX}.failed.hint`);
  if (failure.status === 403) return t(`${PREFIX}.forbidden.hint`);
  if (failure.status === 404) return t(`${PREFIX}.gone.hint`);
  if (failure.code === 'batch.too_many_operations') return t(`${PREFIX}.tooMany.hint`);
  return t(`${PREFIX}.rejected.hint`);
}
