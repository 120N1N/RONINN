import React, { createContext, useContext, useState, useEffect } from 'react';

const ThemeContext = createContext();

export const FONT_OPTIONS = [
  { id: 'inter', name: 'Inter (Modern Sans)', family: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif" },
  { id: 'jetbrains', name: 'JetBrains Mono (Hacker / Cyber)', family: "'JetBrains Mono', 'Courier New', monospace" },
  { id: 'outfit', name: 'Outfit (Sleek Geometric)', family: "'Outfit', 'Inter', sans-serif" },
  { id: 'plus-jakarta', name: 'Plus Jakarta Sans (Crisp Tech)', family: "'Plus Jakarta Sans', sans-serif" },
];

export const FONT_SIZE_OPTIONS = [
  { id: 'xs', name: 'Mini (Paling Kecil)', scale: '67%', factor: 0.67, label: '67%' },
  { id: 'sm', name: 'Kecil (Compact)', scale: '87.5%', factor: 0.875, label: '87%' },
  { id: 'base', name: 'Normal (Default)', scale: '100%', factor: 1.0, label: '100%' },
  { id: 'md', name: 'Sedang (Medium)', scale: '112.5%', factor: 1.125, label: '112%' },
  { id: 'lg', name: 'Besar (Large)', scale: '125%', factor: 1.25, label: '125%' },
  { id: 'xl', name: 'Ekstra Besar (XL)', scale: '137.5%', factor: 1.375, label: '137%' },
];

export const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('corvus_theme') || 'dark';
  });

  const [fontFamily, setFontFamily] = useState(() => {
    return localStorage.getItem('corvus_font_family') || 'inter';
  });

  const [fontSize, setFontSize] = useState(() => {
    return localStorage.getItem('corvus_font_size') || 'base';
  });

  // Apply Theme with Slow & Smooth Transition
  useEffect(() => {
    const root = document.documentElement;

    // Skip transition animation on initial page load
    if (!root.dataset.themeLoaded) {
      root.classList.remove('dark', 'light');
      root.classList.add(theme);
      root.dataset.themeLoaded = 'true';
      localStorage.setItem('corvus_theme', theme);
      return;
    }

    const applyTheme = () => {
      root.classList.remove('dark', 'light');
      root.classList.add(theme);
      localStorage.setItem('corvus_theme', theme);
    };

    // Activate smooth transition class across all elements
    root.classList.add('theme-transitioning');

    // Use native View Transitions API if supported for cinematic smooth crossfade
    if (typeof document.startViewTransition === 'function') {
      try {
        document.startViewTransition(() => {
          applyTheme();
        });
      } catch (e) {
        applyTheme();
      }
    } else {
      applyTheme();
    }

    const timeout = setTimeout(() => {
      root.classList.remove('theme-transitioning');
    }, 800);

    return () => clearTimeout(timeout);
  }, [theme]);

  // Apply Font Family & True Visual Scale across Entire App
  useEffect(() => {
    const root = document.documentElement;
    const body = document.body;
    const selectedFont = FONT_OPTIONS.find(f => f.id === fontFamily) || FONT_OPTIONS[0];
    const selectedSize = FONT_SIZE_OPTIONS.find(s => s.id === fontSize) || FONT_SIZE_OPTIONS.find(s => s.id === 'base') || FONT_SIZE_OPTIONS[2];

    root.style.setProperty('--app-font-family', selectedFont.family);
    root.style.setProperty('--app-font-scale', selectedSize.scale);
    root.style.setProperty('--app-scale-factor', String(selectedSize.factor || 1));

    // Ensure html/body have no zoom or weird scroll traps
    root.style.zoom = '';
    body.style.zoom = '';

    // Apply true visual zoom directly to #root without overflowing width
    const factor = selectedSize.factor || 1;
    const rootContainer = document.getElementById('root');
    if (rootContainer) {
      if (factor === 1) {
        rootContainer.style.zoom = '';
      } else {
        rootContainer.style.zoom = String(factor);
      }
      rootContainer.style.width = '100%';
      rootContainer.style.maxWidth = '100%';
      rootContainer.style.overflowX = 'hidden';
      rootContainer.style.minHeight = '100vh';
    }

    localStorage.setItem('corvus_font_family', fontFamily);
    localStorage.setItem('corvus_font_size', fontSize);
  }, [fontFamily, fontSize]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        setTheme,
        toggleTheme,
        fontFamily,
        setFontFamily,
        fontSize,
        setFontSize,
        FONT_OPTIONS,
        FONT_SIZE_OPTIONS,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
