'use client';

/**
 * Sorting Controls
 * Dropdown for sorting documents by various fields
 */

import { Fragment } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { ChevronDownIcon, ArrowsUpDownIcon } from '@heroicons/react/24/outline';
import clsx from 'clsx';

export type SortOption = {
    label: string;
    field: string;
    order: 'asc' | 'desc';
};

const SORT_OPTIONS: SortOption[] = [
    { label: 'Name (A–Z)', field: 'filename', order: 'asc' },
    { label: 'Name (Z–A)', field: 'filename', order: 'desc' },
    { label: 'Newest first', field: 'created_at', order: 'desc' },
    { label: 'Oldest first', field: 'created_at', order: 'asc' },
    { label: 'Page count (high to low)', field: 'page_count', order: 'desc' },
    { label: 'Page count (low to high)', field: 'page_count', order: 'asc' },
    { label: 'File size (largest)', field: 'file_size_mb', order: 'desc' },
    { label: 'File size (smallest)', field: 'file_size_mb', order: 'asc' },
    { label: 'File type', field: 'file_type', order: 'asc' },
];

const DEFAULT_SORT_OPTION: SortOption = SORT_OPTIONS[2]!; // Newest first

interface SortingControlsProps {
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
    onSortChange: (field: string, order: 'asc' | 'desc') => void;
}

export function SortingControls({ sortBy, sortOrder, onSortChange }: SortingControlsProps) {
    const currentOption = SORT_OPTIONS.find(
        (opt) => opt.field === sortBy && opt.order === sortOrder
    ) ?? DEFAULT_SORT_OPTION;

    return (
        <Menu as="div" className="relative">
            <Menu.Button className="flex items-center gap-2 rounded-lg border border-neutral-200 bg-white px-3 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-50 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700">
                <ArrowsUpDownIcon className="h-4 w-4" />
                <span>{currentOption.label}</span>
                <ChevronDownIcon className="h-4 w-4" />
            </Menu.Button>

            <Transition
                as={Fragment}
                enter="transition ease-out duration-100"
                enterFrom="transform opacity-0 scale-95"
                enterTo="transform opacity-100 scale-100"
                leave="transition ease-in duration-75"
                leaveFrom="transform opacity-100 scale-100"
                leaveTo="transform opacity-0 scale-95"
            >
                <Menu.Items className="absolute right-0 z-10 mt-2 w-56 origin-top-right rounded-lg border border-neutral-200 bg-white shadow-lg focus:outline-none dark:border-neutral-700 dark:bg-neutral-800">
                    <div className="py-1">
                        {SORT_OPTIONS.map((option) => (
                            <Menu.Item key={`${option.field}-${option.order}`}>
                                {({ active }) => (
                                    <button
                                        onClick={() => onSortChange(option.field, option.order)}
                                        className={clsx(
                                            'block w-full px-4 py-2 text-left text-sm',
                                            active
                                                ? 'bg-neutral-100 text-neutral-900 dark:bg-neutral-700 dark:text-white'
                                                : 'text-neutral-700 dark:text-neutral-300',
                                            option.field === sortBy &&
                                            option.order === sortOrder &&
                                            'font-medium text-blue-600 dark:text-blue-400'
                                        )}
                                    >
                                        {option.label}
                                    </button>
                                )}
                            </Menu.Item>
                        ))}
                    </div>
                </Menu.Items>
            </Transition>
        </Menu>
    );
}
