'use client';

import { useEffect } from 'react';
import { useAuthStore } from '../store/authStore';

export default function ThemeSync() {
  const theme = useAuthStore((state) => state.theme);
  const setTheme = useAuthStore((state) => state.setTheme);

  useEffect(() => {
    // Re-trigger theme application on client-side mount
    setTheme(theme);
  }, [theme, setTheme]);

  return null;
}
