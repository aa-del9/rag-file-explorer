'use client';

/**
 * Main navigation component for Document Explorer
 */

import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import clsx from 'clsx';
import {
    FolderOpenIcon,
    MagnifyingGlassIcon,
    Cog6ToothIcon,
    Bars3Icon,
    XMarkIcon,
} from '@heroicons/react/24/outline';
import { useState, useRef, useEffect } from 'react';
import { useDebounce } from '@/lib/hooks';
import { useQuery } from '@tanstack/react-query';
import { searchDocuments } from '@/lib/api';
import { DocumentCard } from '@/components/documents';

const navigation = [
    { name: 'Explorer', href: '/explorer', icon: FolderOpenIcon },
    { name: 'Search', href: '/search', icon: MagnifyingGlassIcon },
];

export function Navbar() {
    const pathname = usePathname();
    const router = useRouter();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [searchQuery, setSearchQuery] = useState('');
    const [showResults, setShowResults] = useState(false);
    const debouncedQuery = useDebounce(searchQuery, 300);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Close dropdown on outside click
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setShowResults(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const { data: searchResults, isLoading } = useQuery({
        queryKey: ['navbar-search', debouncedQuery],
        queryFn: () => searchDocuments({ query: debouncedQuery, top_k: 5 }),
        enabled: debouncedQuery.length > 1,
    });

    const handleSearchSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (searchQuery.trim()) {
            router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
            setShowResults(false);
        }
    };

    return (
        <nav className="sticky top-0 z-50 border-b border-neutral-200 bg-white/80 backdrop-blur-lg dark:border-neutral-800 dark:bg-neutral-900/80">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="flex h-16 items-center justify-between gap-4">
                    {/* Logo */}
                    <div className="flex items-center">
                        <Link href="/" className="flex items-center gap-2">
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
                                <FolderOpenIcon className="h-5 w-5 text-white" />
                            </div>
                            <span className="hidden text-lg font-semibold text-neutral-900 dark:text-white sm:block">
                                RAG Explorer
                            </span>
                        </Link>
                    </div>

                    {/* Global Search Bar */}
                    <div ref={dropdownRef} className="relative flex-1 max-w-md hidden md:block">
                        <form onSubmit={handleSearchSubmit}>
                            <div className="relative">
                                <MagnifyingGlassIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
                                <input
                                    type="text"
                                    placeholder="Search documents..."
                                    value={searchQuery}
                                    onChange={(e) => {
                                        setSearchQuery(e.target.value);
                                        setShowResults(true);
                                    }}
                                    onFocus={() => setShowResults(true)}
                                    className="w-full rounded-lg border border-neutral-200 bg-neutral-50 py-2 pl-10 pr-4 text-sm text-neutral-900 placeholder:text-neutral-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-white dark:placeholder:text-neutral-400"
                                />
                            </div>
                        </form>

                        {/* Search Results Dropdown */}
                        {showResults && debouncedQuery.length > 1 && (
                            <div className="absolute left-0 right-0 top-full mt-2 rounded-lg border border-neutral-200 bg-white shadow-lg dark:border-neutral-700 dark:bg-neutral-900">
                                {isLoading ? (
                                    <div className="p-4 text-center text-sm text-neutral-500">
                                        Searching...
                                    </div>
                                ) : searchResults?.documents?.length ? (
                                    <div className="max-h-96 overflow-y-auto">
                                        {searchResults.documents.map((doc) => (
                                            <Link
                                                key={doc.document_id}
                                                href={`/explorer/${doc.document_id}`}
                                                onClick={() => setShowResults(false)}
                                                className="block border-b border-neutral-100 p-3 hover:bg-neutral-50 dark:border-neutral-800 dark:hover:bg-neutral-800"
                                            >
                                                <div className="font-medium text-neutral-900 dark:text-white">
                                                    {doc.display_name}
                                                </div>
                                                {doc.preview_snippet && (
                                                    <p className="mt-1 line-clamp-2 text-xs text-neutral-500 dark:text-neutral-400">
                                                        {doc.preview_snippet}
                                                    </p>
                                                )}
                                            </Link>
                                        ))}
                                        <Link
                                            href={`/search?q=${encodeURIComponent(searchQuery)}`}
                                            onClick={() => setShowResults(false)}
                                            className="block p-3 text-center text-sm font-medium text-blue-600 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-neutral-800"
                                        >
                                            View all results
                                        </Link>
                                    </div>
                                ) : (
                                    <div className="p-4 text-center text-sm text-neutral-500">
                                        No documents found
                                    </div>
                                )}
                            </div>
                        )}
                    </div>

                    {/* Desktop Navigation */}
                    <div className="hidden md:flex md:items-center md:gap-1">
                        {navigation.map((item) => {
                            const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`);
                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    className={clsx(
                                        'flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                                        isActive
                                            ? 'bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-white'
                                            : 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-white'
                                    )}
                                >
                                    <item.icon className="h-4 w-4" />
                                    {item.name}
                                </Link>
                            );
                        })}
                    </div>

                    {/* Right side actions */}
                    <div className="flex items-center gap-4">
                        {/* Settings Button */}
                        <button
                            className="hidden rounded-lg p-2 text-neutral-500 hover:bg-neutral-100 hover:text-neutral-700 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-neutral-200 md:block"
                            aria-label="Settings"
                        >
                            <Cog6ToothIcon className="h-5 w-5" />
                        </button>

                        {/* Mobile menu button */}
                        <button
                            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                            className="rounded-lg p-2 text-neutral-500 hover:bg-neutral-100 hover:text-neutral-700 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-neutral-200 md:hidden"
                        >
                            {mobileMenuOpen ? (
                                <XMarkIcon className="h-6 w-6" />
                            ) : (
                                <Bars3Icon className="h-6 w-6" />
                            )}
                        </button>
                    </div>
                </div>
            </div>

            {/* Mobile Navigation */}
            {mobileMenuOpen && (
                <div className="border-t border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900 md:hidden">
                    <div className="space-y-1 px-4 py-3">
                        {/* Mobile Search */}
                        <form onSubmit={handleSearchSubmit} className="mb-3">
                            <div className="relative">
                                <MagnifyingGlassIcon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-neutral-400" />
                                <input
                                    type="text"
                                    placeholder="Search documents..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="w-full rounded-lg border border-neutral-200 bg-neutral-50 py-2 pl-10 pr-4 text-sm text-neutral-900 placeholder:text-neutral-500 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-neutral-700 dark:bg-neutral-800 dark:text-white dark:placeholder:text-neutral-400"
                                />
                            </div>
                        </form>

                        {navigation.map((item) => {
                            const isActive = pathname === item.href || pathname?.startsWith(`${item.href}/`);
                            return (
                                <Link
                                    key={item.name}
                                    href={item.href}
                                    onClick={() => setMobileMenuOpen(false)}
                                    className={clsx(
                                        'flex items-center gap-3 rounded-lg px-3 py-2 text-base font-medium',
                                        isActive
                                            ? 'bg-neutral-100 text-neutral-900 dark:bg-neutral-800 dark:text-white'
                                            : 'text-neutral-600 hover:bg-neutral-50 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-white'
                                    )}
                                >
                                    <item.icon className="h-5 w-5" />
                                    {item.name}
                                </Link>
                            );
                        })}
                    </div>
                </div>
            )}
        </nav>
    );
}
