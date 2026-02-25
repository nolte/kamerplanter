import { useEffect } from 'react';

export function useDocumentTitle(title: string) {
  useEffect(() => {
    document.title = `${title} — Kamerplanter`;
    return () => {
      document.title = 'Kamerplanter';
    };
  }, [title]);
}
