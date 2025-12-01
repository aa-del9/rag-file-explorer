import { Metadata } from 'next';
import { Suspense } from 'react';

export const metadata: Metadata = {
  title: 'Search Documents | DocuSearch',
  description: 'Search through your documents using natural language queries powered by AI',
};

export default function SearchLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <Suspense fallback={<SearchLoadingFallback />}>
      {children}
    </Suspense>
  );
}

function SearchLoadingFallback() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8 text-center">
        <div className="mx-auto h-8 w-48 animate-pulse rounded bg-neutral-200 dark:bg-neutral-700" />
        <div className="mx-auto mt-2 h-4 w-64 animate-pulse rounded bg-neutral-200 dark:bg-neutral-700" />
      </div>
      <div className="mx-auto max-w-2xl">
        <div className="h-12 animate-pulse rounded-lg bg-neutral-200 dark:bg-neutral-700" />
      </div>
    </div>
  );
}
