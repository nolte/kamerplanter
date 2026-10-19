/**
 * The two actions on a standing plant (REQ-053 GP-FR-068/069), shared by the planting list and the
 * plan's marker panel: "Correct position" (a new geometry for the plant's slot) and "Transplant to …"
 * (the existing `transplant` task). The dialogs load when one is opened.
 */
import { lazy, Suspense } from 'react';
import { useTranslation } from 'react-i18next';
import { useNotification } from '@/hooks/useNotification';
import type { BedSummary } from '../bed/types';

const PositionCorrectionDialog = lazy(() => import('./PositionCorrectionDialog'));
const TransplantDialog = lazy(() => import('./TransplantDialog'));

export interface PlantActionTarget {
  action: 'correct' | 'transplant';
  plantKey: string;
  /** The plant's slot; `null` for a plant without one (it has no position to correct). */
  slotKey: string | null;
  plantLabel: string;
}

interface PlantActionHostProps {
  bed: BedSummary;
  target: PlantActionTarget | null;
  onClose: () => void;
  /** The slot or the task changed; reload what shows it. */
  onChanged: () => void;
}

export default function PlantActionHost({ bed, target, onClose, onChanged }: PlantActionHostProps) {
  const { t } = useTranslation();
  const notification = useNotification();
  if (!target) return null;

  if (target.action === 'correct' && target.slotKey && bed.geometry) {
    return (
      <Suspense fallback={null}>
        <PositionCorrectionDialog
          bedName={bed.name}
          bedGeometry={bed.geometry}
          bedKey={bed.key}
          slotKey={target.slotKey}
          plantLabel={target.plantLabel}
          onClose={onClose}
          onCorrected={() => {
            notification.success(t('pages.bed.planting.position.done', { plant: target.plantLabel }));
            onChanged();
            onClose();
          }}
        />
      </Suspense>
    );
  }
  if (target.action === 'transplant') {
    return (
      <Suspense fallback={null}>
        <TransplantDialog
          siteKey={bed.site_key}
          bedKey={bed.key}
          plantKey={target.plantKey}
          plantLabel={target.plantLabel}
          onClose={onClose}
          onCreated={(targetName) => {
            notification.success(t('pages.bed.planting.transplant.done', { plant: target.plantLabel, bed: targetName }));
            onChanged();
            onClose();
          }}
        />
      </Suspense>
    );
  }
  return null;
}
