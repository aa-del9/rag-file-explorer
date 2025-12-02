'use client';

/**
 * DocumentCard component
 * Displays document metadata in a card format
 */

import Link from 'next/link';
import clsx from 'clsx';
import { DocumentMetadata } from '@/lib/types';
import { FileTypeIcon, FileTypeBadge } from './file-type-icon';
import {
    CalendarIcon,
    DocumentTextIcon,
    ClockIcon,
} from '@heroicons/react/24/outline';

interface DocumentCardProps {
    document: DocumentMetadata;
    variant?: 'grid' | 'list';
    onDelete?: (id: string) => void;
}

/**
 * Format file size for display
 */
function formatFileSize(sizeInMb: number): string {
    if (sizeInMb < 1) {
        return `${(sizeInMb * 1024).toFixed(0)} KB`;
    }
    return `${sizeInMb.toFixed(1)} MB`;
}

/**
 * Format date for display
 */
function formatDate(dateString: string): string {
    if (!dateString) return 'Unknown';

    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    } catch {
        return dateString;
    }
}

/**
 * Truncate text to a maximum length
 */
function truncateText(text: string | null, maxLength: number): string {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.slice(0, maxLength).trim() + '...';
}

export function DocumentCard({
    document,
    variant = 'grid',
    onDelete,
}: DocumentCardProps) {
    const {
        document_id,
        filename,
        display_name,
        file_type,
        file_size_mb,
        page_count,
        created_at,
        modified_at,
        ai_summary,
        preview_snippet,
        ai_document_type,
    } = document;

    const previewText = preview_snippet || ai_summary;

    if (variant === 'list') {
        return (
            <div className="group flex items-center gap-4 rounded-lg border border-neutral-200 bg-white p-4 transition-all hover:border-neutral-300 hover:shadow-md dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-neutral-700">
                {/* File Icon */}
                <div className="flex-shrink-0">
                    <FileTypeIcon fileType={file_type} size="lg" />
                </div>

                {/* Content */}
                <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                        <Link
                            href={`/explorer/${document_id}`}
                            className="truncate font-medium text-neutral-900 hover:text-blue-600 dark:text-neutral-100 dark:hover:text-blue-400"
                        >
                            {display_name}
                        </Link>
                        <FileTypeBadge fileType={file_type} />
                    </div>

                    {previewText && (
                        <p className="mt-1 line-clamp-1 text-sm text-neutral-600 dark:text-neutral-400">
                            {truncateText(previewText, 150)}
                        </p>
                    )}

                    <div className="mt-2 flex items-center gap-4 text-xs text-neutral-500 dark:text-neutral-500">
                        <span className="flex items-center gap-1">
                            <CalendarIcon className="h-3.5 w-3.5" />
                            {formatDate(created_at)}
                        </span>
                        {page_count && (
                            <span className="flex items-center gap-1">
                                <DocumentTextIcon className="h-3.5 w-3.5" />
                                {page_count} pages
                            </span>
                        )}
                        <span>{formatFileSize(file_size_mb)}</span>
                    </div>
                </div>

                {/* Actions */}
                <div className="flex-shrink-0 opacity-0 transition-opacity group-hover:opacity-100">
                    <Link
                        href={`/explorer/${document_id}`}
                        className="rounded-md bg-neutral-100 px-3 py-1.5 text-sm font-medium text-neutral-700 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700"
                    >
                        View
                    </Link>
                </div>
            </div>
        );
    }

    // Grid variant (default)
    return (
        <div className="group flex flex-col rounded-lg border border-neutral-200 bg-white p-4 transition-all hover:border-neutral-300 hover:shadow-md dark:border-neutral-800 dark:bg-neutral-900 dark:hover:border-neutral-700">
            {/* Header */}
            <div className="flex items-start justify-between gap-2">
                <FileTypeIcon fileType={file_type} size="md" />
                <FileTypeBadge fileType={file_type} />
            </div>

            {/* Title */}
            <Link
                href={`/explorer/${document_id}`}
                className="mt-3 line-clamp-2 font-medium text-neutral-900 hover:text-blue-600 dark:text-neutral-100 dark:hover:text-blue-400"
            >
                {display_name}
            </Link>

            {/* Preview */}
            {previewText && (
                <p className="mt-2 line-clamp-3 flex-1 text-sm text-neutral-600 dark:text-neutral-400">
                    {truncateText(previewText, 200)}
                </p>
            )}

            {/* Document Type Badge */}
            {ai_document_type && (
                <div className="mt-3">
                    <span className="inline-flex items-center rounded-full bg-purple-100 px-2 py-0.5 text-xs font-medium text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                        {ai_document_type}
                    </span>
                </div>
            )}

            {/* Metadata Footer */}
            <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-neutral-100 pt-3 text-xs text-neutral-500 dark:border-neutral-800 dark:text-neutral-500">
                <span className="flex items-center gap-1">
                    <CalendarIcon className="h-3.5 w-3.5" />
                    {formatDate(created_at)}
                </span>
                {page_count && (
                    <span className="flex items-center gap-1">
                        <DocumentTextIcon className="h-3.5 w-3.5" />
                        {page_count} pages
                    </span>
                )}
                <span>{formatFileSize(file_size_mb)}</span>
            </div>
        </div>
    );
}

/**
 * Document card skeleton for loading state
 */
export function DocumentCardSkeleton({ variant = 'grid' }: { variant?: 'grid' | 'list' }) {
    if (variant === 'list') {
        return (
            <div className="flex animate-pulse items-center gap-4 rounded-lg border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
                <div className="h-12 w-12 rounded-lg bg-neutral-200 dark:bg-neutral-700" />
                <div className="flex-1 space-y-2">
                    <div className="h-4 w-3/4 rounded bg-neutral-200 dark:bg-neutral-700" />
                    <div className="h-3 w-1/2 rounded bg-neutral-200 dark:bg-neutral-700" />
                </div>
            </div>
        );
    }

    return (
        <div className="animate-pulse rounded-lg border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
            <div className="flex items-start justify-between">
                <div className="h-8 w-8 rounded-lg bg-neutral-200 dark:bg-neutral-700" />
                <div className="h-5 w-12 rounded-full bg-neutral-200 dark:bg-neutral-700" />
            </div>
            <div className="mt-3 h-5 w-3/4 rounded bg-neutral-200 dark:bg-neutral-700" />
            <div className="mt-2 space-y-2">
                <div className="h-3 w-full rounded bg-neutral-200 dark:bg-neutral-700" />
                <div className="h-3 w-5/6 rounded bg-neutral-200 dark:bg-neutral-700" />
                <div className="h-3 w-2/3 rounded bg-neutral-200 dark:bg-neutral-700" />
            </div>
            <div className="mt-4 flex gap-3 border-t border-neutral-100 pt-3 dark:border-neutral-800">
                <div className="h-3 w-20 rounded bg-neutral-200 dark:bg-neutral-700" />
                <div className="h-3 w-16 rounded bg-neutral-200 dark:bg-neutral-700" />
            </div>
        </div>
    );
}
