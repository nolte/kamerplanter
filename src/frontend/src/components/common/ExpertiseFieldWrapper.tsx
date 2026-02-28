import type { ReactNode } from 'react';
import type { ExperienceLevel } from '@/api/types';
import { useExpertiseLevel } from '@/hooks/useExpertiseLevel';

interface ExpertiseFieldWrapperProps {
  minLevel: ExperienceLevel;
  children: ReactNode;
}

export default function ExpertiseFieldWrapper({
  minLevel,
  children,
}: ExpertiseFieldWrapperProps) {
  const { isFieldVisible } = useExpertiseLevel();

  if (!isFieldVisible(minLevel)) return null;
  return <>{children}</>;
}
