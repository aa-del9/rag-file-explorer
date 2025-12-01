'use client';

/**
 * File type icon component
 * Displays appropriate icon based on file type
 */

import { DocumentTextIcon, DocumentIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

interface FileTypeIconProps {
    fileType: string;
    className?: string;
    size?: 'sm' | 'md' | 'lg';
}

const sizeClasses = {
    sm: 'h-6 w-6',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
};

// Color classes based on file type
const colorClasses: Record<string, string> = {
    '.pdf': 'text-red-500',
    '.doc': 'text-blue-500',
    '.docx': 'text-blue-500',
    '.txt': 'text-gray-500',
    '.md': 'text-purple-500',
    default: 'text-gray-400',
};

export function FileTypeIcon({
    fileType,
    className,
    size = 'md',
}: FileTypeIconProps) {
    const normalizedType = fileType.toLowerCase();
    const colorClass = colorClasses[normalizedType] || colorClasses.default;

    // Use DocumentTextIcon for text-based documents
    const isTextDocument = ['.pdf', '.doc', '.docx', '.txt', '.md'].includes(normalizedType);
    const IconComponent = isTextDocument ? DocumentTextIcon : DocumentIcon;

    return (
        <IconComponent
            className={clsx(sizeClasses[size], colorClass, className)}
            aria-label={`${fileType} file`}
        />
    );
}

/**
 * File type badge component
 */
export function FileTypeBadge({ fileType }: { fileType: string }) {
    const normalizedType = fileType.toLowerCase().replace('.', '').toUpperCase();

    const badgeColors: Record<string, string> = {
        PDF: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
        DOC: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
        DOCX: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
        TXT: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400',
    };

    const colorClass = badgeColors[normalizedType] || 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400';

    return (
        <span
            className={clsx(
                'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
                colorClass
            )}
        >
            {normalizedType}
        </span>
    );
}
