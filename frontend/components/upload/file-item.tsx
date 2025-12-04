'use client';

/**
 * FileItem component for displaying upload queue items
 * Shows file info, status badge, and progress indicator
 */

import {
    DocumentIcon,
    DocumentTextIcon,
    XMarkIcon,
    ArrowPathIcon,
    CheckCircleIcon,
    ExclamationCircleIcon,
    ClockIcon,
} from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { formatFileSize, getFileExtension } from '@/lib/api/upload';
import type { QueuedFile, UploadStatus } from '@/lib/hooks/use-upload-queue';

interface FileItemProps {
    item: QueuedFile;
    onRemove: (id: string) => void;
    onRetry: (id: string) => void;
}

/**
 * Get file icon based on extension
 */
function FileIcon({ extension }: { extension: string }) {
    const isPdf = extension === '.pdf';

    return (
        <div
            className={clsx(
                'flex h-10 w-10 items-center justify-center rounded-lg',
                isPdf ? 'bg-red-100 dark:bg-red-900/30' : 'bg-blue-100 dark:bg-blue-900/30'
            )}
        >
            {isPdf ? (
                <DocumentTextIcon className="h-5 w-5 text-red-600 dark:text-red-400" />
            ) : (
                <DocumentIcon className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            )}
        </div>
    );
}

/**
 * Status badge component
 */
function StatusBadge({ status }: { status: UploadStatus }) {
    const config: Record<
        UploadStatus,
        { label: string; className: string; icon: React.ElementType }
    > = {
        pending: {
            label: 'Pending',
            className: 'bg-neutral-100 text-neutral-700 dark:bg-neutral-800 dark:text-neutral-300',
            icon: ClockIcon,
        },
        uploading: {
            label: 'Uploading...',
            className: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
            icon: ArrowPathIcon,
        },
        completed: {
            label: 'Completed',
            className: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
            icon: CheckCircleIcon,
        },
        failed: {
            label: 'Failed',
            className: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
            icon: ExclamationCircleIcon,
        },
    };

    const { label, className, icon: Icon } = config[status];

    return (
        <span
            className={clsx(
                'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium',
                className
            )}
        >
            <Icon
                className={clsx('h-3.5 w-3.5', status === 'uploading' && 'animate-spin')}
            />
            {label}
        </span>
    );
}

/**
 * Progress bar component
 */
function ProgressBar({ progress, status }: { progress: number; status: UploadStatus }) {
    if (status === 'completed' || status === 'failed') return null;

    return (
        <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-neutral-200 dark:bg-neutral-700">
            <div
                className={clsx(
                    'h-full rounded-full transition-all duration-300',
                    status === 'uploading'
                        ? 'bg-blue-500 animate-pulse'
                        : 'bg-neutral-300 dark:bg-neutral-600'
                )}
                style={{ width: status === 'uploading' ? '100%' : `${progress}%` }}
            />
        </div>
    );
}

/**
 * FileItem component
 */
export function FileItem({ item, onRemove, onRetry }: FileItemProps) {
    const extension = getFileExtension(item.file.name);
    const canRemove = item.status !== 'uploading';
    const canRetry = item.status === 'failed';

    return (
        <div
            className={clsx(
                'group relative rounded-lg border p-4 transition-all',
                item.status === 'completed' &&
                'border-green-200 bg-green-50/50 dark:border-green-800/50 dark:bg-green-900/10',
                item.status === 'failed' &&
                'border-red-200 bg-red-50/50 dark:border-red-800/50 dark:bg-red-900/10',
                item.status === 'uploading' &&
                'border-blue-200 bg-blue-50/50 dark:border-blue-800/50 dark:bg-blue-900/10',
                item.status === 'pending' &&
                'border-neutral-200 bg-white dark:border-neutral-700 dark:bg-neutral-800/50'
            )}
        >
            <div className="flex items-start gap-3">
                {/* File Icon */}
                <FileIcon extension={extension} />

                {/* File Info */}
                <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                        <h4 className="truncate text-sm font-medium text-neutral-900 dark:text-white">
                            {item.file.name}
                        </h4>
                        <StatusBadge status={item.status} />
                    </div>

                    <div className="mt-1 flex items-center gap-2 text-xs text-neutral-500 dark:text-neutral-400">
                        <span>{formatFileSize(item.file.size)}</span>
                        <span>•</span>
                        <span className="uppercase">{extension.replace('.', '')}</span>
                    </div>

                    {/* Error message */}
                    {item.error && (
                        <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                            {item.error}
                        </p>
                    )}

                    {/* Success info */}
                    {item.status === 'completed' && item.response && (
                        <p className="mt-1 text-xs text-green-600 dark:text-green-400">
                            Processed in {item.response.processing_time_seconds?.toFixed(1)}s •{' '}
                            {item.response.chunk_count} chunks
                        </p>
                    )}

                    {/* Progress bar */}
                    <ProgressBar progress={item.progress} status={item.status} />
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1">
                    {canRetry && (
                        <button
                            onClick={() => onRetry(item.id)}
                            className="rounded-md p-1.5 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-600 dark:hover:bg-neutral-700 dark:hover:text-neutral-300"
                            title="Retry upload"
                        >
                            <ArrowPathIcon className="h-4 w-4" />
                        </button>
                    )}
                    {canRemove && (
                        <button
                            onClick={() => onRemove(item.id)}
                            className="rounded-md p-1.5 text-neutral-400 hover:bg-neutral-100 hover:text-red-600 dark:hover:bg-neutral-700 dark:hover:text-red-400"
                            title="Remove from queue"
                        >
                            <XMarkIcon className="h-4 w-4" />
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
