import type { ReactNode } from 'react';
import Box from '@mui/material/Box';
import HelpTooltip from '@/components/common/HelpTooltip';

interface FieldHelpProps {
  /** Glossary key (`glossary.<term>.*`). Without it the field renders unchanged. */
  helpTerm?: string;
  /**
   * `input` aligns the icon with an outlined text input (dense margin + floating
   * label), `inline` centres it on a single line such as a switch label.
   */
  variant?: 'input' | 'inline';
  children: ReactNode;
}

/**
 * The help slot of the `Form*Field` components (#3020, UI-NFR-011 §2.2/§6.1,
 * UI-NFR-008 R-042/R-043).
 *
 * The `HelpTooltip` trigger is rendered as a *sibling* of the field, never inside
 * its `<label>`: a button inside the label would join the input's accessible name
 * and a click on it would also focus/toggle the control. Next to the field the
 * label keeps its `for`/`id` association untouched, and the trigger is its own
 * named focus stop in the tab order right after the input.
 *
 * Without `helpTerm` the children are returned as they are, so the 700+
 * existing call sites keep their exact DOM.
 */
export default function FieldHelp({ helpTerm, variant = 'input', children }: FieldHelpProps) {
  if (!helpTerm) return <>{children}</>;

  if (variant === 'inline') {
    return (
      <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.25, maxWidth: '100%' }}>
        {children}
        <HelpTooltip term={helpTerm} iconOnly />
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 0.5, minWidth: 0 }}>
      <Box sx={{ flexGrow: 1, minWidth: 0 }}>{children}</Box>
      {/* margin="dense" puts the 40px input 8px down; 2 × 8px centres the ~26px trigger on it. */}
      <Box sx={{ flexShrink: 0, mt: 2 }}>
        <HelpTooltip term={helpTerm} iconOnly />
      </Box>
    </Box>
  );
}
