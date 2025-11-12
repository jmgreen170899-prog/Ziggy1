'use client';

export default function NewsLoading() {
  return (
    <div className="space-y-6" aria-busy>
      <div className="h-8 w-32 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
      <div className="space-y-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="rounded-lg border bg-white dark:bg-gray-900 p-4">
            <div className="h-5 w-3/4 bg-gray-200 dark:bg-gray-800 rounded animate-pulse mb-2" />
            <div className="h-4 w-1/2 bg-gray-200 dark:bg-gray-800 rounded animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}
