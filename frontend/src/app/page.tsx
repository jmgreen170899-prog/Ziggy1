import React, { Suspense } from 'react';
import { CardSkeleton } from '@/components/ui/Loading';

// Lazy load the heavy AdvancedDashboard component
const AdvancedDashboard = React.lazy(() => import('@/components/AdvancedDashboard'));

export default function Home() {
  // Enhanced Dashboard with all new visual improvements
  return (
    <div>
      {/* Enhanced Dashboard with all new features */}
      <Suspense 
        fallback={
          <div className="space-y-6 p-6">
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
              <div className="lg:col-span-3 space-y-6">
                <CardSkeleton showHeader contentLines={4} className="h-64" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <CardSkeleton showHeader contentLines={3} />
                  <CardSkeleton showHeader contentLines={3} />
                </div>
              </div>
              <div className="space-y-6">
                <CardSkeleton showHeader contentLines={2} />
                <CardSkeleton showHeader contentLines={4} />
                <CardSkeleton showHeader contentLines={3} />
              </div>
            </div>
          </div>
        }
      >
        <AdvancedDashboard />
      </Suspense>
    </div>
  );
}
