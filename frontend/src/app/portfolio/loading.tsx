'use client';

export default function PortfolioLoading() {
  return (
    <div className="space-y-6" aria-busy>
      <div className="h-8 w-44 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="rounded-lg border bg-white dark:bg-gray-900 p-4 space-y-3">
          <div className="h-5 w-1/2 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
          <div className="h-32 w-full bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
        </div>
        <div className="rounded-lg border bg-white dark:bg-gray-900 p-4 space-y-3">
          <div className="h-5 w-1/3 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
          <div className="h-32 w-full bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
        </div>
        <div className="rounded-lg border bg-white dark:bg-gray-900 p-4 space-y-3">
          <div className="h-5 w-1/4 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
          <div className="h-32 w-full bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
        </div>
      </div>
      <div className="rounded-lg border bg-white dark:bg-gray-900 p-4 space-y-2">
        <div className="h-5 w-24 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-10 w-full bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
        ))}
      </div>
    </div>
  );
}
