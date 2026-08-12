import React, { useEffect } from 'react';
import { Toaster } from 'sonner';
import { useStore, applyThemeClass } from './store/useStore';
import { LandingPage } from './components/landing/LandingPage';
import { Dashboard } from './components/dashboard/Dashboard';
import { CommandPalette } from './components/common/CommandPalette';

export default function App() {
  const { activeTab, theme } = useStore();

  useEffect(() => {
    applyThemeClass(theme);
  }, [theme]);

  return (
    <>
      <Toaster position="top-right" richColors />
      <CommandPalette />
      {activeTab === 'landing' ? <LandingPage /> : <Dashboard />}
    </>
  );
}

