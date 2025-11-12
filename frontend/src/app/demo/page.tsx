'use client';

import React, { useState } from 'react';
import { IntroGate } from '@/features/intro';
import AdvancedDashboard from '@/components/AdvancedDashboard';

export default function Demo() {
  const [forceShow, setForceShow] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [version, setVersion] = useState('1.0.0');
  const [showAdvancedDashboard, setShowAdvancedDashboard] = useState(false);

  const triggerIntro = () => {
    // Clear storage and force show
    localStorage.removeItem(`ziggy_intro_seen_v${version}`);
    setForceShow(true);
    setTimeout(() => setForceShow(false), 100);
  };

  if (showAdvancedDashboard) {
    return <AdvancedDashboard />;
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">ZiggyClean Demo</h1>
      
      <div className="space-y-4 mb-6">
        <div>
          <label htmlFor="theme" className="block text-sm font-medium mb-2">
            Theme
          </label>
          <select
            id="theme"
            value={theme}
            onChange={(e) => setTheme(e.target.value as 'light' | 'dark')}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="light">Light</option>
            <option value="dark">Dark</option>
          </select>
        </div>

        <div>
          <label htmlFor="version" className="block text-sm font-medium mb-2">
            App Version
          </label>
          <input
            id="version"
            type="text"
            value={version}
            onChange={(e) => setVersion(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md"
          />
        </div>
      </div>

      <div className="space-x-4">
        <button
          onClick={triggerIntro}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
        >
          Trigger Intro
        </button>

        <button
          onClick={() => setShowAdvancedDashboard(!showAdvancedDashboard)}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
        >
          {showAdvancedDashboard ? 'Hide' : 'Show'} Advanced Dashboard
        </button>

        <button
          onClick={() => {
            localStorage.removeItem(`ziggy_intro_seen_v${version}`);
            window.location.reload();
          }}
          className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
        >
          Clear Storage & Reload
        </button>
      </div>

      <div className="mt-6 p-4 bg-gray-50 rounded-md">
        <h2 className="font-semibold mb-2">Instructions:</h2>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Use &ldquo;Trigger Intro&rdquo; to force show the animation</li>
          <li>• Click &ldquo;Show Advanced Dashboard&rdquo; to preview the enhanced dashboard with AI insights, sparklines, and advanced metrics</li>
          <li>• Try different themes to see visual variations</li>
          <li>• Change version to reset the &ldquo;seen&rdquo; status</li>
          <li>• Press Esc during animation to skip</li>
          <li>• Test on different devices for responsive behavior</li>
        </ul>
      </div>

      {/* Hidden IntroGate for demo purposes */}
      {forceShow && (
        <IntroGate
          appVersion={version}
          theme={theme}
          forceShow={true}
          onDone={() => {
            console.log('Intro completed!');
            setForceShow(false);
          }}
        >
          <div />
        </IntroGate>
      )}
    </div>
  );
}