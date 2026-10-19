/**
 * Category icons of field mode (REQ-053 §18.1 step 4: category icon ≥ 32 px). The icon is never the only
 * cue - every row and chip also prints the category's name.
 */
import type { SvgIconComponent } from '@mui/icons-material';
import AgricultureIcon from '@mui/icons-material/Agriculture';
import BugReportIcon from '@mui/icons-material/BugReport';
import BuildIcon from '@mui/icons-material/Build';
import ContentCutIcon from '@mui/icons-material/ContentCut';
import EditNoteIcon from '@mui/icons-material/EditNote';
import GrassIcon from '@mui/icons-material/Grass';
import LocalFloristIcon from '@mui/icons-material/LocalFlorist';
import ScienceIcon from '@mui/icons-material/Science';
import SpaIcon from '@mui/icons-material/Spa';
import TaskAltIcon from '@mui/icons-material/TaskAlt';
import VisibilityIcon from '@mui/icons-material/Visibility';
import WaterDropIcon from '@mui/icons-material/WaterDrop';
import YardIcon from '@mui/icons-material/Yard';
import type { QuickChipId } from './quickChips';

/** Minimum icon edge in field mode (§18.1 step 4). */
export const FIELD_ICON_PX = 32;

const BY_CATEGORY: Readonly<Record<string, SvgIconComponent>> = {
  watering: WaterDropIcon,
  flush: WaterDropIcon,
  rainfall: WaterDropIcon,
  feeding: ScienceIcon,
  ec_check: ScienceIcon,
  ph_adjustment: ScienceIcon,
  soil_amendment: ScienceIcon,
  liming: ScienceIcon,
  harvest: AgricultureIcon,
  sowing: SpaIcon,
  pricking_out: SpaIcon,
  thinning: SpaIcon,
  transplant: LocalFloristIcon,
  weeding: YardIcon,
  mulching: YardIcon,
  hilling: GrassIcon,
  tillage: GrassIcon,
  soil_loosening: GrassIcon,
  pruning: ContentCutIcon,
  pest_control: BugReportIcon,
  observation: VisibilityIcon,
  maintenance: BuildIcon,
  note: EditNoteIcon,
};

export function categoryIcon(category: string): SvgIconComponent {
  return BY_CATEGORY[category] ?? TaskAltIcon;
}

export function chipIcon(id: QuickChipId): SvgIconComponent {
  return id === 'planted' ? LocalFloristIcon : categoryIcon(id);
}
