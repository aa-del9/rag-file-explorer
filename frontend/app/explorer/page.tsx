'use client';

/**
 * Document Explorer Page
 * Main file browser view with search, filtering, and sorting
 */

import { useState, useMemo, useCallback } from 'react';
import { useDocuments } from '@/lib/hooks';
import { DocumentList, DocumentSearchBar, FileTypeFilter } from '@/components/documents';
import { SortField, SortOrder, DocumentsQueryParams } from '@/lib/types';
import { ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

export default function ExplorerPage() {
    // Query parameters
    const [params, setParams] = useState<DocumentsQueryParams>({
        page: 1,
        page_size: 20,
        sort_by: 'created_at',
        sort_order: 'desc',
    });

    // Local filter states
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedFileTypes, setSelectedFileTypes] = useState<string[]>([]);
    const [viewVariant, setViewVariant] = useState<'grid' | 'list'>('grid');

    // Fetch documents
    const {
        data,
        isLoading,
        isError,
        error,
        refetch,
        isFetching,
    } = useDocuments(params);

    // Filter documents client-side based on search and file type filters
    const filteredDocuments = useMemo(() => {
        if (!data?.documents) return [];

        let filtered = data.documents;

        // Filter by search query (filename)
        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            filtered = filtered.filter(
                (doc) =>
                    doc.filename.toLowerCase().includes(query) ||
                    doc.ai_summary?.toLowerCase().includes(query) ||
                    doc.preview_snippet?.toLowerCase().includes(query)
            );
        }

        // Filter by file types
        if (selectedFileTypes.length > 0) {
            filtered = filtered.filter((doc) =>
                selectedFileTypes.includes(doc.file_type.toLowerCase())
            );
        }

        return filtered;
    }, [data?.documents, searchQuery, selectedFileTypes]);

    // Handle sort change
    const handleSortChange = useCallback((field: SortField, order: SortOrder) => {
        setParams((prev) => ({
            ...prev,
            sort_by: field,
            sort_order: order,
        }));
    }, []);

    // Handle page change
    const handlePageChange = useCallback((page: number) => {
        setParams((prev) => ({
            ...prev,
            page,
        }));
    }, []);

    return (
        <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
                    Document Explorer
                </h1>
                <p className="mt-2 text-neutral-600 dark:text-neutral-400">
                    Browse, search, and manage your documents
                </p>
            </div>

            {/* Search and Filters */}
            <div className="mb-6 space-y-4">
                <DocumentSearchBar
                    value={searchQuery}
                    onChange={setSearchQuery}
                    placeholder="Search by filename or content..."
                    className="max-w-xl"
                />

                <div className="flex flex-wrap items-center justify-between gap-4">
                    <FileTypeFilter
                        selectedTypes={selectedFileTypes}
                        onChange={setSelectedFileTypes}
                    />

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

            {/* Error State */}
            {isError && (
                <div className="mb-6 flex items-center gap-3 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-900/20">
                    <ExclamationTriangleIcon className="h-5 w-5 flex-shrink-0 text-red-500" />
                    <div>
                        <p className="font-medium text-red-800 dark:text-red-400">
                            Failed to load documents
                        </p>
                        <p className="mt-1 text-sm text-red-700 dark:text-red-300">
                            {error?.message || 'An unexpected error occurred'}
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

            {/* Document List */}
            <DocumentList
                documents={filteredDocuments}
                isLoading={isLoading}
                variant={viewVariant}
                onVariantChange={setViewVariant}
                sortBy={params.sort_by}
                sortOrder={params.sort_order}
                onSortChange={handleSortChange}
                emptyMessage={
                    searchQuery || selectedFileTypes.length > 0
                        ? 'No documents match your filters'
                        : 'No documents uploaded yet'
                }
            />

            {/* Pagination */}
            {data && data.total_pages > 1 && (
                <div className="mt-8 flex items-center justify-center gap-2">
                    <button
                        onClick={() => handlePageChange(data.page - 1)}
                        disabled={data.page <= 1}
                        className="rounded-lg border border-neutral-200 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
                    >
                        Previous
                    </button>

                    <span className="px-4 text-sm text-neutral-600 dark:text-neutral-400">
                        Page {data.page} of {data.total_pages}
                    </span>

                    <button
                        onClick={() => handlePageChange(data.page + 1)}
                        disabled={data.page >= data.total_pages}
                        className="rounded-lg border border-neutral-200 px-4 py-2 text-sm font-medium text-neutral-700 transition-colors hover:bg-neutral-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
                    >
                        Next
                    </button>
                </div>
            )}

            {/* Stats Footer */}
            {data && (
                <div className="mt-8 border-t border-neutral-200 pt-4 text-center text-sm text-neutral-500 dark:border-neutral-700 dark:text-neutral-400">
                    Showing {filteredDocuments.length} of {data.total_documents} documents
                </div>
            )}
        </div>
    );
}
