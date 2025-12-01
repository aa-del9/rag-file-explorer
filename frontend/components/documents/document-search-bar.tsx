'use client';

/**
 * Search/filter bar for documents
 */

import { useState, useCallback } from 'react';
import { MagnifyingGlassIcon, XMarkIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

interface DocumentSearchBarProps {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
    className?: string;
}

export function DocumentSearchBar({
    value,
    onChange,
    placeholder = 'Search documents...',
    className,
}: DocumentSearchBarProps) {
    const [isFocused, setIsFocused] = useState(false);

    const handleClear = useCallback(() => {
        onChange('');
    }, [onChange]);

    return (
        <div
            className={clsx(
                'relative flex items-center rounded-lg border transition-all',
                isFocused
                    ? 'border-blue-500 ring-2 ring-blue-500/20'
                    : 'border-neutral-200 dark:border-neutral-700',
                'bg-white dark:bg-neutral-900',
                className
            )}
        >
            <MagnifyingGlassIcon className="ml-3 h-5 w-5 flex-shrink-0 text-neutral-400" />

            <input
                type="text"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                placeholder={placeholder}
                className="w-full bg-transparent px-3 py-2.5 text-sm text-neutral-900 placeholder-neutral-400 focus:outline-none dark:text-neutral-100 dark:placeholder-neutral-500"
            />

            {value && (
                <button
                    onClick={handleClear}
                    className="mr-2 rounded-md p-1 text-neutral-400 hover:bg-neutral-100 hover:text-neutral-600 dark:hover:bg-neutral-800 dark:hover:text-neutral-300"
                    aria-label="Clear search"
                >
                    <XMarkIcon className="h-4 w-4" />
                </button>
            )}
        </div>
    );
}

/**
 * File type filter pills
 */
interface FileTypeFilterProps {
    selectedTypes: string[];
    onChange: (types: string[]) => void;
    availableTypes?: string[];
}

const defaultFileTypes = ['.pdf', '.doc', '.docx'];

export function FileTypeFilter({
    selectedTypes,
    onChange,
    availableTypes = defaultFileTypes,
}: FileTypeFilterProps) {
    const toggleType = (type: string) => {
        if (selectedTypes.includes(type)) {
            onChange(selectedTypes.filter((t) => t !== type));
        } else {
            onChange([...selectedTypes, type]);
        }
    };

    return (
        <div className="flex flex-wrap gap-2">
            <span className="text-sm text-neutral-500 dark:text-neutral-400">
                File type:
            </span>
            {availableTypes.map((type) => (
                <button
                    key={type}
                    onClick={() => toggleType(type)}
                    className={clsx(
                        'rounded-full px-3 py-1 text-xs font-medium transition-colors',
                        selectedTypes.includes(type)
                            ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                            : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-400 dark:hover:bg-neutral-700'
                    )}
                >
                    {type.replace('.', '').toUpperCase()}
                </button>
            ))}
            {selectedTypes.length > 0 && (
                <button
                    onClick={() => onChange([])}
                    className="text-xs text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200"
                >
                    Clear
                </button>
            )}
        </div>
    );
}
