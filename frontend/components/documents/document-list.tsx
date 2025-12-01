'use client';

/**
 * DocumentList component
 * Displays a list/grid of documents with sorting controls
 */

import { useState } from 'react';
import clsx from 'clsx';
import { DocumentMetadata, SortField, SortOrder } from '@/lib/types';
import { DocumentCard, DocumentCardSkeleton } from './document-card';
import {
    Squares2X2Icon,
    ListBulletIcon,
    ChevronUpIcon,
    ChevronDownIcon,
    FunnelIcon,
} from '@heroicons/react/24/outline';

interface DocumentListProps {
    documents: DocumentMetadata[];
    isLoading?: boolean;
    variant?: 'grid' | 'list';
    onVariantChange?: (variant: 'grid' | 'list') => void;
    sortBy?: SortField;
    sortOrder?: SortOrder;
    onSortChange?: (field: SortField, order: SortOrder) => void;
    emptyMessage?: string;
}

interface SortOption {
    label: string;
    field: SortField;
}

const sortOptions: SortOption[] = [
    { label: 'Name', field: 'filename' },
    { label: 'Date Created', field: 'created_at' },
    { label: 'Date Modified', field: 'modified_at' },
    { label: 'Size', field: 'file_size_mb' },
    { label: 'Pages', field: 'page_count' },
];

export function DocumentList({
    documents,
    isLoading = false,
    variant = 'grid',
    onVariantChange,
    sortBy = 'created_at',
    sortOrder = 'desc',
    onSortChange,
    emptyMessage = 'No documents found',
}: DocumentListProps) {
    const [localVariant, setLocalVariant] = useState<'grid' | 'list'>(variant);
    const [localSortBy, setLocalSortBy] = useState<SortField>(sortBy);
    const [localSortOrder, setLocalSortOrder] = useState<SortOrder>(sortOrder);

    const currentVariant = onVariantChange ? variant : localVariant;
    const currentSortBy = onSortChange ? sortBy : localSortBy;
    const currentSortOrder = onSortChange ? sortOrder : localSortOrder;

    const handleVariantChange = (newVariant: 'grid' | 'list') => {
        if (onVariantChange) {
            onVariantChange(newVariant);
        } else {
            setLocalVariant(newVariant);
        }
    };

    const handleSortChange = (field: SortField) => {
        let newOrder: SortOrder = 'desc';

        if (field === currentSortBy) {
            // Toggle order if same field
            newOrder = currentSortOrder === 'asc' ? 'desc' : 'asc';
        }

        if (onSortChange) {
            onSortChange(field, newOrder);
        } else {
            setLocalSortBy(field);
            setLocalSortOrder(newOrder);
        }
    };

    // Sort documents locally if no external handler
    const sortedDocuments = onSortChange
        ? documents
        : [...documents].sort((a, b) => {
            let comparison = 0;

            switch (currentSortBy) {
                case 'filename':
                    comparison = a.filename.localeCompare(b.filename);
                    break;
                case 'created_at':
                    comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
                    break;
                case 'modified_at':
                    comparison = new Date(a.modified_at).getTime() - new Date(b.modified_at).getTime();
                    break;
                case 'file_size_mb':
                    comparison = a.file_size_mb - b.file_size_mb;
                    break;
                case 'page_count':
                    comparison = (a.page_count || 0) - (b.page_count || 0);
                    break;
            }

            return currentSortOrder === 'asc' ? comparison : -comparison;
        });

    return (
        <div className="space-y-4">
            {/* Controls */}
            <div className="flex flex-wrap items-center justify-between gap-4">
                {/* Sort Controls */}
                <div className="flex flex-wrap items-center gap-2">
                    <span className="text-sm text-neutral-500 dark:text-neutral-400">
                        Sort by:
                    </span>
                    <div className="flex flex-wrap gap-1">
                        {sortOptions.map((option) => (
                            <button
                                key={option.field}
                                onClick={() => handleSortChange(option.field)}
                                className={clsx(
                                    'flex items-center gap-1 rounded-md px-2 py-1 text-sm transition-colors',
                                    currentSortBy === option.field
                                        ? 'bg-neutral-900 text-white dark:bg-white dark:text-neutral-900'
                                        : 'bg-neutral-100 text-neutral-700 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700'
                                )}
                            >
                                {option.label}
                                {currentSortBy === option.field && (
                                    currentSortOrder === 'asc' ? (
                                        <ChevronUpIcon className="h-3 w-3" />
                                    ) : (
                                        <ChevronDownIcon className="h-3 w-3" />
                                    )
                                )}
                            </button>
                        ))}
                    </div>
                </div>

                {/* View Toggle */}
                <div className="flex items-center gap-1 rounded-lg bg-neutral-100 p-1 dark:bg-neutral-800">
                    <button
                        onClick={() => handleVariantChange('grid')}
                        className={clsx(
                            'rounded-md p-1.5 transition-colors',
                            currentVariant === 'grid'
                                ? 'bg-white text-neutral-900 shadow-sm dark:bg-neutral-700 dark:text-white'
                                : 'text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200'
                        )}
                        aria-label="Grid view"
                    >
                        <Squares2X2Icon className="h-4 w-4" />
                    </button>
                    <button
                        onClick={() => handleVariantChange('list')}
                        className={clsx(
                            'rounded-md p-1.5 transition-colors',
                            currentVariant === 'list'
                                ? 'bg-white text-neutral-900 shadow-sm dark:bg-neutral-700 dark:text-white'
                                : 'text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200'
                        )}
                        aria-label="List view"
                    >
                        <ListBulletIcon className="h-4 w-4" />
                    </button>
                </div>
            </div>

            {/* Document Count */}
            {!isLoading && (
                <p className="text-sm text-neutral-500 dark:text-neutral-400">
                    {sortedDocuments.length} document{sortedDocuments.length !== 1 ? 's' : ''}
                </p>
            )}

            {/* Loading State */}
            {isLoading && (
                <div
                    className={clsx(
                        currentVariant === 'grid'
                            ? 'grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
                            : 'space-y-3'
                    )}
                >
                    {Array.from({ length: 8 }).map((_, i) => (
                        <DocumentCardSkeleton key={i} variant={currentVariant} />
                    ))}
                </div>
            )}

            {/* Empty State */}
            {!isLoading && sortedDocuments.length === 0 && (
                <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-neutral-200 py-16 dark:border-neutral-700">
                    <FunnelIcon className="h-12 w-12 text-neutral-300 dark:text-neutral-600" />
                    <p className="mt-4 text-lg font-medium text-neutral-600 dark:text-neutral-400">
                        {emptyMessage}
                    </p>
                    <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-500">
                        Try adjusting your filters or upload new documents.
                    </p>
                </div>
            )}

            {/* Documents */}
            {!isLoading && sortedDocuments.length > 0 && (
                <div
                    className={clsx(
                        currentVariant === 'grid'
                            ? 'grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
                            : 'space-y-3'
                    )}
                >
                    {sortedDocuments.map((doc) => (
                        <DocumentCard
                            key={doc.document_id}
                            document={doc}
                            variant={currentVariant}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}
