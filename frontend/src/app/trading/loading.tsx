'use client';

export default function TradingLoading() {
  return (
    <div className="space-y-6" aria-busy>
      <div className="h-8 w-36 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="rounded-lg border bg-white dark:bg-gray-900 p-4 space-y-3">
            <div className="h-5 w-1/3 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
            <div className="h-24 w-full bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
            <div className="h-4 w-1/2 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}
