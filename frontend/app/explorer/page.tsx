'use client';

/**
 * Document Explorer Page
 * Main file browser view with search, filtering, and sorting
 */

import { useState, useMemo, useCallback } from 'react';
import { useDocuments } from '@/lib/hooks';
import { useSearchManager } from '@/lib/hooks';
import {
    DocumentList,
    DocumentSearchBar,
    FiltersPanel,
    SortingControls,
} from '@/components/documents';
import { SortField, SortOrder, DocumentsQueryParams } from '@/lib/types';
import {
    ExclamationTriangleIcon,
    ArrowPathIcon,
    Bars3BottomLeftIcon,
    Squares2X2Icon,
} from '@heroicons/react/24/outline';

export default function ExplorerPage() {
    // View state
    const [viewVariant, setViewVariant] = useState<'grid' | 'list'>('grid');
    const [showFilters, setShowFilters] = useState(true);

    // Search manager handles query, filters, sorting, pagination
    const search = useSearchManager();

    // Query parameters for base document list (when no search/filters)
    const [params, setParams] = useState<DocumentsQueryParams>({
        page: 1,
        page_size: 20,
        sort_by: 'created_at',
        sort_order: 'desc',
    });

    // Fetch base documents (when no active search)
    const {
        data: baseData,
        isLoading: baseLoading,
        isError: baseError,
        error: baseErrorData,
        refetch: baseRefetch,
        isFetching: baseFetching,
    } = useDocuments(params);

    // Determine if we're in search mode
    const hasActiveSearch =
        !!search.debouncedQuery ||
        (search.filters.file_types?.length ?? 0) > 0 ||
        !!search.filters.created_after ||
        !!search.filters.created_before ||
        search.filters.min_pages !== undefined ||
        search.filters.max_pages !== undefined ||
        search.filters.min_size_mb !== undefined ||
        search.filters.max_size_mb !== undefined ||
        (search.filters.tags?.length ?? 0) > 0;

    // Use search results if searching, otherwise base documents
    const documents = hasActiveSearch
        ? search.results?.documents ?? []
        : baseData?.documents ?? [];

    const isLoading = hasActiveSearch ? search.isLoading : baseLoading;
    const isError = hasActiveSearch ? search.isError : baseError;
    const error = hasActiveSearch ? search.error : baseErrorData;
    const refetch = hasActiveSearch ? search.refetch : baseRefetch;
    const isFetching = hasActiveSearch ? search.isLoading : baseFetching;

    // Client-side sorting (already sorted by backend for base, but apply for consistency)
    const sortedDocuments = useMemo(() => {
        const docs = [...documents];
        const field = hasActiveSearch ? search.sortBy : params.sort_by;
        const order = hasActiveSearch ? search.sortOrder : params.sort_order;

        if (!field) return docs;

        docs.sort((a, b) => {
            let aVal: any;
            let bVal: any;

            switch (field) {
                case 'filename':
                    aVal = a.display_name?.toLowerCase() ?? '';
                    bVal = b.display_name?.toLowerCase() ?? '';
                    break;
                case 'created_at':
                    aVal = a.created_at ?? '';
                    bVal = b.created_at ?? '';
                    break;
                case 'page_count':
                    aVal = a.page_count ?? 0;
                    bVal = b.page_count ?? 0;
                    break;
                case 'file_size_mb':
                    aVal = a.file_size_mb ?? 0;
                    bVal = b.file_size_mb ?? 0;
                    break;
                case 'file_type':
                    aVal = a.file_type ?? '';
                    bVal = b.file_type ?? '';
                    break;
                default:
                    return 0;
            }

            if (aVal < bVal) return order === 'asc' ? -1 : 1;
            if (aVal > bVal) return order === 'asc' ? 1 : -1;
            return 0;
        });

        return docs;
    }, [documents, hasActiveSearch, search.sortBy, search.sortOrder, params.sort_by, params.sort_order]);

    // Handle sort change
    const handleSortChange = useCallback(
        (field: string, order: 'asc' | 'desc') => {
            if (hasActiveSearch) {
                search.setSortBy(field);
                search.setSortOrder(order);
            } else {
                setParams((prev) => ({
                    ...prev,
                    sort_by: field as SortField,
                    sort_order: order as SortOrder,
                }));
            }
        },
        [hasActiveSearch, search]
    );

    // Handle page change
    const handlePageChange = useCallback((page: number) => {
        setParams((prev) => ({
            ...prev,
            page,
        }));
    }, []);

    const totalDocs = hasActiveSearch
        ? search.results?.total_results ?? 0
        : baseData?.total_documents ?? 0;

    return (
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            {/* Header */}
            <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
                        Document Explorer
                    </h1>
                    <p className="mt-1 text-neutral-600 dark:text-neutral-400">
                        Browse, search, and manage your documents
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    {/* View Toggle */}
                    <div className="flex rounded-lg border border-neutral-200 dark:border-neutral-700">
                        <button
                            onClick={() => setViewVariant('grid')}
                            className={`rounded-l-lg p-2 ${viewVariant === 'grid'
                                ? 'bg-neutral-100 text-neutral-900 dark:bg-neutral-700 dark:text-white'
                                : 'text-neutral-500 hover:bg-neutral-50 dark:text-neutral-400 dark:hover:bg-neutral-800'
                                }`}
                            aria-label="Grid view"
                        >
                            <Squares2X2Icon className="h-5 w-5" />
                        </button>
                        <button
                            onClick={() => setViewVariant('list')}
                            className={`rounded-r-lg p-2 ${viewVariant === 'list'
                                ? 'bg-neutral-100 text-neutral-900 dark:bg-neutral-700 dark:text-white'
                                : 'text-neutral-500 hover:bg-neutral-50 dark:text-neutral-400 dark:hover:bg-neutral-800'
                                }`}
                            aria-label="List view"
                        >
                            <Bars3BottomLeftIcon className="h-5 w-5" />
                        </button>
                    </div>

                    {/* Refresh Button */}
                    <button
                        onClick={() => refetch()}
                        disabled={isFetching}
                        className="flex items-center gap-2 rounded-lg bg-neutral-100 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-200 disabled:opacity-50 dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700"
                    >
                        <ArrowPathIcon
                            className={`h-4 w-4 ${isFetching ? 'animate-spin' : ''}`}
                        />
                        Refresh
                    </button>
                </div>
            </div>

            <div className="flex gap-6">
                {/* Filters Sidebar */}
                {showFilters && (
                    <aside className="hidden w-64 flex-shrink-0 lg:block">
                        <FiltersPanel
                            filters={search.filters}
                            onChange={search.setFilters}
                            onReset={search.resetFilters}
                        />
                    </aside>
                )}

                {/* Main Content */}
                <div className="flex-1">
                    {/* Search and Sort Bar */}
                    <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                        <DocumentSearchBar
                            value={search.query}
                            onChange={search.setQuery}
                            placeholder="Search by filename or content..."
                            className="max-w-md"
                        />

                        <div className="flex items-center gap-3">
                            {/* <button
                                onClick={() => setShowFilters(!showFilters)}
                                className="flex items-center gap-2 rounded-lg border border-neutral-200 px-3 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800 lg:hidden"
                            >
                                Filters
                            </button> */}

                            {/* <SortingControls
                                sortBy={hasActiveSearch ? search.sortBy : params.sort_by}
                                sortOrder={hasActiveSearch ? search.sortOrder : params.sort_order}
                                onSortChange={handleSortChange}
                            /> */}
                        </div>
                    </div>

                    {/* Error State */}
                    {isError && (
                        <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-900/20">
                            <ExclamationTriangleIcon className="h-5 w-5 flex-shrink-0 text-red-500" />
                            <div>
                                <p className="font-medium text-red-800 dark:text-red-400">
                                    Failed to load documents
                                </p>
                                <p className="mt-1 text-sm text-red-700 dark:text-red-300">
                                    {(error as any)?.message || 'An unexpected error occurred'}
                                </p>
                            </div>
                            <button
                                onClick={() => refetch()}
                                className="ml-auto rounded-md bg-red-100 px-3 py-1.5 text-sm font-medium text-red-800 hover:bg-red-200 dark:bg-red-900/30 dark:text-red-400 dark:hover:bg-red-900/50"
                            >
                                Retry
                            </button>
                        </div>
                    )}

                    {/* Search mode indicator */}
                    {hasActiveSearch && (
                        <div className="mb-4 flex items-center justify-between rounded-lg bg-blue-50 px-4 py-2 dark:bg-blue-900/20">
                            <span className="text-sm text-blue-700 dark:text-blue-400">
                                {search.results?.search_type === 'semantic' && '🔮 Semantic search'}
                                {search.results?.search_type === 'metadata' && '📋 Metadata search'}
                                {search.results?.search_type === 'hybrid' && '🔀 Hybrid search'}
                                {!search.results?.search_type && 'Searching...'}
                                {search.results?.processing_time_ms && (
                                    <span className="ml-2 text-blue-500">
                                        ({search.results.processing_time_ms.toFixed(0)}ms)
                                    </span>
                                )}
                            </span>
                            <button
                                onClick={() => {
                                    search.setQuery('');
                                    search.resetFilters();
                                }}
                                className="text-sm font-medium text-blue-600 hover:text-blue-700 dark:text-blue-400"
                            >
                                Clear search
                            </button>
                        </div>
                    )}

                    {/* Document List */}
                    <DocumentList
                        documents={sortedDocuments}
                        isLoading={isLoading}
                        variant={viewVariant}
                        onVariantChange={setViewVariant}
                        emptyMessage={
                            hasActiveSearch
                                ? 'No documents match your filters'
                                : 'No documents uploaded yet'
                        }
                    />

                    {/* Pagination (for base documents) */}
                    {!hasActiveSearch && baseData && baseData.total_pages > 1 && (
                        <div className="mt-8 flex items-center justify-center gap-2">
                            <button
                                onClick={() => handlePageChange(baseData.page - 1)}
                                disabled={baseData.page <= 1}
                                className="rounded-lg border border-neutral-200 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
                            >
                                Previous
                            </button>

                            <span className="px-4 text-sm text-neutral-600 dark:text-neutral-400">
                                Page {baseData.page} of {baseData.total_pages}
                            </span>

                            <button
                                onClick={() => handlePageChange(baseData.page + 1)}
                                disabled={baseData.page >= baseData.total_pages}
                                className="rounded-lg border border-neutral-200 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
                            >
                                Next
                            </button>
                        </div>
                    )}

                    {/* Stats Footer */}
                    <div className="mt-8 border-t border-neutral-200 pt-4 text-center text-sm text-neutral-500 dark:border-neutral-700 dark:text-neutral-400">
                        Showing {sortedDocuments.length} of {totalDocs} documents
                    </div>
                </div>
            </div>
        </div>
    );
}
