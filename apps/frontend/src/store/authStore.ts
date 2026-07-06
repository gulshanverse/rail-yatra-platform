import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface User {
  id: string;
  email: string;
  fullName: string;
  phone?: string | null;
  role: string;
  settings?: {
    theme: string;
    notifications: boolean;
    language: string;
  };
  subscriptions?: Array<{
    tier: 'FREE' | 'PREMIUM' | 'PREMIUM_PLUS';
    credits: number;
    status: string;
  }>;
}

interface AuthState {
  token: string | null;
  user: User | null;
  theme: 'light' | 'dark' | 'auto';
  setAuth: (token: string, user: User) => void;
  clearAuth: () => void;
  setTheme: (theme: 'light' | 'dark' | 'auto') => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      theme: 'auto',
      setAuth: (token, user) => set({ token, user }),
      clearAuth: () => set({ token: null, user: null }),
      setTheme: (theme) => {
        set({ theme });
        // Update DOM for tailwind dark class
        if (typeof window !== 'undefined') {
          const root = window.document.documentElement;
          root.classList.remove('light', 'dark');
          if (theme === 'auto') {
            const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            root.classList.add(systemTheme);
          } else {
            root.classList.add(theme);
          }
        }
      },
    }),
    {
      name: 'railyatra-auth-storage',
    }
  )
);
