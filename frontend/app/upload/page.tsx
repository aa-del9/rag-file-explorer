'use client';

/**
 * Upload Page
 * Multi-file upload with drag-and-drop and upload queue
 */

import { useCallback, useEffect } from 'react';
import Link from 'next/link';
import {
    ArrowUpTrayIcon,
    TrashIcon,
    XCircleIcon,
    FolderOpenIcon,
    CheckCircleIcon,
    ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { Dropzone, FileItem } from '@/components/upload';
import { useUploadQueue } from '@/lib/hooks/use-upload-queue';
import clsx from 'clsx';

export default function UploadPage() {
    const {
        queue,
        addFiles,
        removeFile,
        startUpload,
        clearCompleted,
        clearAll,
        retryFile,
        cancelUpload,
        isUploading,
        totalFiles,
        completedFiles,
        failedFiles,
        pendingFiles,
    } = useUploadQueue();

    // Auto-start upload when files are added
    const handleFilesSelected = useCallback(
        (files: FileList | File[]) => {
            addFiles(files);
        },
        [addFiles]
    );

    // Start upload when there are pending files and not currently uploading
    useEffect(() => {
        if (pendingFiles > 0 && !isUploading) {
            startUpload();
        }
    }, [pendingFiles, isUploading, startUpload]);

    const hasFiles = totalFiles > 0;
    const hasCompleted = completedFiles > 0 || failedFiles > 0;
    const allCompleted = hasFiles && pendingFiles === 0 && !isUploading;

    return (
        <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-neutral-900 dark:text-white">
                    Upload Documents
                </h1>
                <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400">
                    Upload PDF, DOC, or DOCX files to add them to your document library.
                    Files are processed with AI to extract metadata, summaries, and keywords.
                </p>
            </div>

            {/* Dropzone Card */}
            <div className="mb-6 overflow-hidden rounded-xl border border-neutral-200 bg-white shadow-sm dark:border-neutral-700 dark:bg-neutral-900">
                <div className="p-6">
                    <Dropzone onFilesSelected={handleFilesSelected} disabled={isUploading} />
                </div>
            </div>

            {/* Upload Queue */}
            {hasFiles && (
                <div className="overflow-hidden rounded-xl border border-neutral-200 bg-white shadow-sm dark:border-neutral-700 dark:bg-neutral-900">
                    {/* Queue Header */}
                    <div className="flex items-center justify-between border-b border-neutral-200 px-6 py-4 dark:border-neutral-700">
                        <div className="flex items-center gap-4">
                            <h2 className="text-lg font-semibold text-neutral-900 dark:text-white">
                                Upload Queue
                            </h2>

                            {/* Stats badges */}
                            <div className="flex items-center gap-2">
                                {completedFiles > 0 && (
                                    <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
                                        <CheckCircleIcon className="h-3.5 w-3.5" />
                                        {completedFiles}
                                    </span>
                                )}
                                {failedFiles > 0 && (
                                    <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-900/30 dark:text-red-400">
                                        <ExclamationTriangleIcon className="h-3.5 w-3.5" />
                                        {failedFiles}
                                    </span>
                                )}
                                {isUploading && (
                                    <span className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                                        <ArrowUpTrayIcon className="h-3.5 w-3.5 animate-bounce" />
                                        Uploading...
                                    </span>
                                )}
                            </div>
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-2">
                            {isUploading && (
                                <button
                                    onClick={cancelUpload}
                                    className="inline-flex items-center gap-1.5 rounded-lg border border-neutral-300 bg-white px-3 py-1.5 text-sm font-medium text-neutral-700 hover:bg-neutral-50 dark:border-neutral-600 dark:bg-neutral-800 dark:text-neutral-200 dark:hover:bg-neutral-700"
                                >
                                    <XCircleIcon className="h-4 w-4" />
                                    Cancel
                                </button>
                            )}
                            {hasCompleted && !isUploading && (
                                <button
                                    onClick={clearCompleted}
                                    className="inline-flex items-center gap-1.5 rounded-lg border border-neutral-300 bg-white px-3 py-1.5 text-sm font-medium text-neutral-700 hover:bg-neutral-50 dark:border-neutral-600 dark:bg-neutral-800 dark:text-neutral-200 dark:hover:bg-neutral-700"
                                >
                                    <TrashIcon className="h-4 w-4" />
                                    Clear Completed
                                </button>
                            )}
                            {!isUploading && totalFiles > 0 && (
                                <button
                                    onClick={clearAll}
                                    className="inline-flex items-center gap-1.5 rounded-lg border border-red-300 bg-white px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 dark:border-red-600 dark:bg-neutral-800 dark:text-red-400 dark:hover:bg-red-900/20"
                                >
                                    <TrashIcon className="h-4 w-4" />
                                    Clear All
                                </button>
                            )}
                        </div>
                    </div>

                    {/* File List */}
                    <div className="divide-y divide-neutral-100 dark:divide-neutral-800">
                        <div className="max-h-[500px] overflow-y-auto p-4">
                            <div className="space-y-3">
                                {queue.map((item) => (
                                    <FileItem
                                        key={item.id}
                                        item={item}
                                        onRemove={removeFile}
                                        onRetry={retryFile}
                                    />
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Queue Footer - Success message */}
                    {allCompleted && completedFiles > 0 && (
                        <div className="border-t border-neutral-200 bg-green-50 px-6 py-4 dark:border-neutral-700 dark:bg-green-900/10">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
                                    <CheckCircleIcon className="h-5 w-5" />
                                    <span className="text-sm font-medium">
                                        {completedFiles} {completedFiles === 1 ? 'file' : 'files'}{' '}
                                        uploaded successfully
                                        {failedFiles > 0 && `, ${failedFiles} failed`}
                                    </span>
                                </div>
                                <Link
                                    href="/explorer"
                                    className="inline-flex items-center gap-1.5 rounded-lg bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 dark:bg-green-700 dark:hover:bg-green-600"
                                >
                                    <FolderOpenIcon className="h-4 w-4" />
                                    View in Explorer
                                </Link>
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* Empty state */}
            {!hasFiles && (
                <div className="rounded-xl border border-dashed border-neutral-300 bg-neutral-50 p-12 text-center dark:border-neutral-600 dark:bg-neutral-800/50">
                    <ArrowUpTrayIcon className="mx-auto h-12 w-12 text-neutral-400" />
                    <h3 className="mt-4 text-sm font-medium text-neutral-900 dark:text-white">
                        No files selected
                    </h3>
                    <p className="mt-2 text-sm text-neutral-500 dark:text-neutral-400">
                        Drag and drop files above or click to browse
                    </p>
                </div>
            )}
        </div>
    );
}
