'use client';

/**
 * Filters Panel
 * Left sidebar with all document filters
 */

import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getTags } from '@/lib/api';
import { DocumentFilters } from '@/lib/types';
import {
    FunnelIcon,
    XMarkIcon,
    ChevronDownIcon,
    ChevronUpIcon,
} from '@heroicons/react/24/outline';

interface FiltersPanelProps {
    filters: DocumentFilters;
    onChange: (partial: Partial<DocumentFilters>) => void;
    onReset: () => void;
}

const FILE_TYPES = [
    { value: '.pdf', label: 'PDF' },
    { value: '.docx', label: 'DOCX' },
    { value: '.txt', label: 'TXT' },
    { value: '.doc', label: 'DOC' },
    { value: '.md', label: 'Markdown' },
];

export function FiltersPanel({ filters, onChange, onReset }: FiltersPanelProps) {
    const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
        fileType: true,
        dateRange: false,
        pageCount: false,
        fileSize: false,
        tags: false,
    });

    const { data: tagsData } = useQuery({
        queryKey: ['documents', 'tags'],
        queryFn: getTags,
    });

    const toggleSection = (section: string) => {
        setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
    };

    const isExpanded = (section: string): boolean => {
        return expandedSections[section] ?? false;
    };

    const activeFilterCount = [
        filters.file_types?.length,
        filters.created_after || filters.created_before,
        filters.min_pages !== undefined || filters.max_pages !== undefined,
        filters.min_size_mb !== undefined || filters.max_size_mb !== undefined,
        filters.tags?.length,
    ].filter(Boolean).length;

    return (
        <div className="rounded-lg border border-neutral-200 bg-white p-4 dark:border-neutral-800 dark:bg-neutral-900">
            {/* Header */}
            <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <FunnelIcon className="h-5 w-5 text-neutral-500" />
                    <span className="font-medium text-neutral-900 dark:text-white">Filters</span>
                    {activeFilterCount > 0 && (
                        <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400">
                            {activeFilterCount}
                        </span>
                    )}
                </div>
                {activeFilterCount > 0 && (
                    <button
                        onClick={onReset}
                        className="text-sm text-neutral-500 hover:text-neutral-700 dark:text-neutral-400 dark:hover:text-neutral-200"
                    >
                        Reset
                    </button>
                )}
            </div>

            <div className="space-y-3">
                {/* File Type Filter */}
                <FilterSection
                    title="File Type"
                    expanded={isExpanded('fileType')}
                    onToggle={() => toggleSection('fileType')}
                >
                    <div className="space-y-2">
                        {FILE_TYPES.map((type) => (
                            <label key={type.value} className="flex items-center gap-2">
                                <input
                                    type="checkbox"
                                    checked={filters.file_types?.includes(type.value) ?? false}
                                    onChange={(e) => {
                                        const current = filters.file_types ?? [];
                                        if (e.target.checked) {
                                            onChange({ file_types: [...current, type.value] });
                                        } else {
                                            onChange({
                                                file_types: current.filter((t) => t !== type.value),
                                            });
                                        }
                                    }}
                                    className="h-4 w-4 rounded border-neutral-300 text-blue-600 focus:ring-blue-500 dark:border-neutral-600 dark:bg-neutral-800"
                                />
                                <span className="text-sm text-neutral-700 dark:text-neutral-300">
                                    {type.label}
                                </span>
                            </label>
                        ))}
                    </div>
                </FilterSection>

                {/* Date Range Filter */}
                <FilterSection
                    title="Date Range"
                    expanded={isExpanded('dateRange')}
                    onToggle={() => toggleSection('dateRange')}
                >
                    <div className="space-y-2">
                        <div>
                            <label className="block text-xs text-neutral-500 dark:text-neutral-400">
                                Created After
                            </label>
                            <input
                                type="date"
                                value={filters.created_after ?? ''}
                                onChange={(e) => onChange({ created_after: e.target.value || undefined })}
                                className="mt-1 w-full rounded border border-neutral-200 bg-neutral-50 px-2 py-1 text-sm dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
                            />
                        </div>
                        <div>
                            <label className="block text-xs text-neutral-500 dark:text-neutral-400">
                                Created Before
                            </label>
                            <input
                                type="date"
                                value={filters.created_before ?? ''}
                                onChange={(e) => onChange({ created_before: e.target.value || undefined })}
                                className="mt-1 w-full rounded border border-neutral-200 bg-neutral-50 px-2 py-1 text-sm dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
                            />
                        </div>
                    </div>
                </FilterSection>

                {/* Page Count Filter */}
                <FilterSection
                    title="Page Count"
                    expanded={isExpanded('pageCount')}
                    onToggle={() => toggleSection('pageCount')}
                >
                    <div className="flex items-center gap-2">
                        <input
                            type="number"
                            placeholder="Min"
                            min={1}
                            value={filters.min_pages ?? ''}
                            onChange={(e) =>
                                onChange({ min_pages: e.target.value ? Number(e.target.value) : undefined })
                            }
                            className="w-full rounded border border-neutral-200 bg-neutral-50 px-2 py-1 text-sm dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
                        />
                        <span className="text-neutral-400">–</span>
                        <input
                            type="number"
                            placeholder="Max"
                            min={1}
                            value={filters.max_pages ?? ''}
                            onChange={(e) =>
                                onChange({ max_pages: e.target.value ? Number(e.target.value) : undefined })
                            }
                            className="w-full rounded border border-neutral-200 bg-neutral-50 px-2 py-1 text-sm dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
                        />
                    </div>
                </FilterSection>

                {/* File Size Filter */}
                <FilterSection
                    title="File Size (MB)"
                    expanded={isExpanded('fileSize')}
                    onToggle={() => toggleSection('fileSize')}
                >
                    <div className="flex items-center gap-2">
                        <input
                            type="number"
                            placeholder="Min"
                            min={0}
                            step={0.1}
                            value={filters.min_size_mb ?? ''}
                            onChange={(e) =>
                                onChange({ min_size_mb: e.target.value ? Number(e.target.value) : undefined })
                            }
                            className="w-full rounded border border-neutral-200 bg-neutral-50 px-2 py-1 text-sm dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
                        />
                        <span className="text-neutral-400">–</span>
                        <input
                            type="number"
                            placeholder="Max"
                            min={0}
                            step={0.1}
                            value={filters.max_size_mb ?? ''}
                            onChange={(e) =>
                                onChange({ max_size_mb: e.target.value ? Number(e.target.value) : undefined })
                            }
                            className="w-full rounded border border-neutral-200 bg-neutral-50 px-2 py-1 text-sm dark:border-neutral-700 dark:bg-neutral-800 dark:text-white"
                        />
                    </div>
                </FilterSection>

                {/* Tags Filter */}
                {/* <FilterSection
                    title="Tags"
                    expanded={isExpanded('tags')}
                    onToggle={() => toggleSection('tags')}
                >
                    {tagsData?.tags?.length ? (
                        <div className="flex flex-wrap gap-2">
                            {tagsData.tags.map((tag) => {
                                const isSelected = filters.tags?.includes(tag);
                                return (
                                    <button
                                        key={tag}
                                        onClick={() => {
                                            const current = filters.tags ?? [];
                                            if (isSelected) {
                                                onChange({ tags: current.filter((t) => t !== tag) });
                                            } else {
                                                onChange({ tags: [...current, tag] });
                                            }
                                        }}
                                        className={`rounded-full px-2 py-0.5 text-xs font-medium transition-colors ${
                                            isSelected
                                                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                                                : 'bg-neutral-100 text-neutral-600 hover:bg-neutral-200 dark:bg-neutral-800 dark:text-neutral-400 dark:hover:bg-neutral-700'
                                        }`}
                                    >
                                        {tag}
                                    </button>
                                );
                            })}
                        </div>
                    ) : (
                        <p className="text-sm text-neutral-500">No tags available</p>
                    )}
                </FilterSection> */}
            </div>
        </div>
    );
}

function FilterSection({
    title,
    expanded,
    onToggle,
    children,
}: {
    title: string;
    expanded: boolean;
    onToggle: () => void;
    children: React.ReactNode;
}) {
    return (
        <div className="border-t border-neutral-100 pt-3 dark:border-neutral-800">
            <button
                onClick={onToggle}
                className="flex w-full items-center justify-between text-left"
            >
                <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                    {title}
                </span>
                {expanded ? (
                    <ChevronUpIcon className="h-4 w-4 text-neutral-400" />
                ) : (
                    <ChevronDownIcon className="h-4 w-4 text-neutral-400" />
                )}
            </button>
            {expanded && <div className="mt-3">{children}</div>}
        </div>
    );
}
