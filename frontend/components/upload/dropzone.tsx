'use client';

/**
 * Dropzone component for drag-and-drop file uploads
 * Supports multiple file selection
 */

import { useCallback, useState, useRef } from 'react';
import { CloudArrowUpIcon, DocumentPlusIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';
import { ALLOWED_EXTENSIONS } from '@/lib/api/upload';

interface DropzoneProps {
    onFilesSelected: (files: FileList | File[]) => void;
    disabled?: boolean;
}

export function Dropzone({ onFilesSelected, disabled = false }: DropzoneProps) {
    const [isDragOver, setIsDragOver] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Handle drag events
    const handleDragEnter = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (!disabled) {
            setIsDragOver(true);
        }
    }, [disabled]);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragOver(false);
    }, []);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (!disabled) {
            setIsDragOver(true);
        }
    }, [disabled]);

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            e.stopPropagation();
            setIsDragOver(false);

            if (disabled) return;

            const { files } = e.dataTransfer;
            if (files && files.length > 0) {
                onFilesSelected(files);
            }
        },
        [disabled, onFilesSelected]
    );

    // Handle file input change
    const handleFileChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>) => {
            const { files } = e.target;
            if (files && files.length > 0) {
                onFilesSelected(files);
            }
            // Reset input so the same file can be selected again
            e.target.value = '';
        },
        [onFilesSelected]
    );

    // Trigger file input click
    const handleClick = useCallback(() => {
        if (!disabled) {
            fileInputRef.current?.click();
        }
    }, [disabled]);

    // Accept string for file input
    const acceptTypes = ALLOWED_EXTENSIONS.join(',');

    return (
        <div
            onDragEnter={handleDragEnter}
            onDragLeave={handleDragLeave}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={handleClick}
            className={clsx(
                'relative cursor-pointer rounded-xl border-2 border-dashed p-8 transition-all duration-200',
                isDragOver && !disabled
                    ? 'border-blue-400 bg-blue-50 dark:border-blue-500 dark:bg-blue-900/20'
                    : 'border-neutral-300 bg-neutral-50 hover:border-blue-400 hover:bg-neutral-100 dark:border-neutral-600 dark:bg-neutral-800/50 dark:hover:border-blue-500 dark:hover:bg-neutral-800',
                disabled && 'cursor-not-allowed opacity-50'
            )}
        >
            {/* Hidden file input */}
            <input
                ref={fileInputRef}
                type="file"
                multiple
                accept={acceptTypes}
                onChange={handleFileChange}
                className="hidden"
                disabled={disabled}
            />

            {/* Dropzone content */}
            <div className="flex flex-col items-center justify-center gap-4 text-center">
                {/* Icon */}
                <div
                    className={clsx(
                        'flex h-16 w-16 items-center justify-center rounded-full transition-colors',
                        isDragOver && !disabled
                            ? 'bg-blue-100 dark:bg-blue-900/30'
                            : 'bg-neutral-200 dark:bg-neutral-700'
                    )}
                >
                    {isDragOver && !disabled ? (
                        <DocumentPlusIcon className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                    ) : (
                        <CloudArrowUpIcon className="h-8 w-8 text-neutral-500 dark:text-neutral-400" />
                    )}
                </div>

                {/* Text */}
                <div>
                    <p className="text-sm font-medium text-neutral-900 dark:text-white">
                        {isDragOver && !disabled
                            ? 'Drop files here'
                            : 'Drag and drop files here'}
                    </p>
                    <p className="mt-1 text-sm text-neutral-500 dark:text-neutral-400">
                        or <span className="text-blue-600 dark:text-blue-400">browse</span> to
                        select files
                    </p>
                </div>

                {/* Supported formats */}
                <p className="text-xs text-neutral-400 dark:text-neutral-500">
                    Supported formats: {ALLOWED_EXTENSIONS.map((ext) => ext.replace('.', '').toUpperCase()).join(', ')}
                </p>
            </div>
        </div>
    );
}
