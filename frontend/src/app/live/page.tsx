/**
 * Live Data Redirect - Redirects to main dashboard with live data integrated
 * The live data functionality has been integrated into the main dashboard and other pages
 */

'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function LiveDataRedirect() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to main dashboard where live data is now integrated
    router.replace('/');
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-gray-900 mb-4">
          🚀 Live Data Now Integrated!
        </h1>
        <p className="text-gray-600 mb-4">
          Live data has been integrated into the main dashboard and portfolio pages.
        </p>
        <p className="text-sm text-gray-500">
          Redirecting to main dashboard...
        </p>
      </div>
    </div>
  );
}