'use client';

/**
 * Search Page - Advanced document search with semantic capabilities
 */

import { useState } from 'react';
import { useSearchDocuments, useDebounce } from '@/lib/hooks';
import { DocumentList, DocumentSearchBar } from '@/components/documents';
import { SearchQueryParams } from '@/lib/types';
import { MagnifyingGlassIcon, SparklesIcon } from '@heroicons/react/24/outline';

export default function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [hasSearched, setHasSearched] = useState(false);
  const debouncedQuery = useDebounce(searchQuery, 400);

  const searchParams: SearchQueryParams = {
    query: debouncedQuery,
    top_k: 20,
    include_chunk_scores: true,
  };

  const {
    data,
    isLoading,
    isError,
    error,
  } = useSearchDocuments(hasSearched ? searchParams : {});

  const handleSearch = () => {
    if (searchQuery.trim()) {
      setHasSearched(true);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8 text-center">
        <h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
          Semantic Search
        </h1>
        <p className="mt-2 text-neutral-600 dark:text-neutral-400">
          Find documents using natural language queries powered by AI
        </p>
      </div>

      {/* Search Input */}
      <div className="mx-auto max-w-2xl">
        <div className="flex gap-2">
          <div className="flex-1" onKeyDown={handleKeyDown}>
            <DocumentSearchBar
              value={searchQuery}
              onChange={setSearchQuery}
              placeholder="Ask a question or describe what you're looking for..."
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={!searchQuery.trim() || isLoading}
            className="flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <MagnifyingGlassIcon className="h-5 w-5" />
            Search
          </button>
        </div>

        {/* Search hints */}
        <div className="mt-4 flex flex-wrap items-center justify-center gap-2 text-sm text-neutral-500 dark:text-neutral-400">
          <SparklesIcon className="h-4 w-4" />
          <span>Try:</span>
          <button
            onClick={() => setSearchQuery('documents about machine learning')}
            className="rounded-full bg-neutral-100 px-3 py-1 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700"
          >
            machine learning
          </button>
          <button
            onClick={() => setSearchQuery('financial reports and analysis')}
            className="rounded-full bg-neutral-100 px-3 py-1 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700"
          >
            financial reports
          </button>
          <button
            onClick={() => setSearchQuery('technical documentation')}
            className="rounded-full bg-neutral-100 px-3 py-1 hover:bg-neutral-200 dark:bg-neutral-800 dark:hover:bg-neutral-700"
          >
            technical docs
          </button>
        </div>
      </div>

      {/* Results */}
      {hasSearched && (
        <div className="mt-12">
          {/* Search info */}
          {data && (
            <div className="mb-6 flex items-center justify-between">
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                Found {data.total_results} results for "{searchQuery}"
                {data.processing_time_ms && (
                  <span className="ml-2 text-neutral-400">
                    ({data.processing_time_ms.toFixed(0)}ms)
                  </span>
                )}
              </p>
              <span className="rounded-full bg-purple-100 px-3 py-1 text-xs font-medium text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                {data.search_type} search
              </span>
            </div>
          )}

          {/* Error State */}
          {isError && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-900/20">
              <p className="text-red-800 dark:text-red-400">
                Search failed: {error?.message || 'An error occurred'}
              </p>
            </div>
          )}

          {/* Results List */}
          <DocumentList
            documents={data?.documents || []}
            isLoading={isLoading}
            emptyMessage="No documents match your search"
          />
        </div>
      )}

      {/* Empty state when no search yet */}
      {!hasSearched && (
        <div className="mt-16 text-center">
          <MagnifyingGlassIcon className="mx-auto h-16 w-16 text-neutral-300 dark:text-neutral-600" />
          <h3 className="mt-4 text-lg font-medium text-neutral-900 dark:text-neutral-100">
            Start searching
          </h3>
          <p className="mt-2 text-neutral-600 dark:text-neutral-400">
            Enter a query above to search across all your documents
          </p>
        </div>
      )}
    </div>
  );
}
