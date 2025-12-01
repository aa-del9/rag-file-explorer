'use client';

/**
 * Main navigation component for Document Explorer
 */

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';
import {
    FolderOpenIcon,
    MagnifyingGlassIcon,
    Cog6ToothIcon,
    Bars3Icon,
    XMarkIcon,
} from '@heroicons/react/24/outline';
import { useState } from 'react';

const navigation = [
    { name: 'Explorer', href: '/explorer', icon: FolderOpenIcon },
    { name: 'Search', href: '/search', icon: MagnifyingGlassIcon },
];

export function Navbar() {
    const pathname = usePathname();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    return (
        <nav className="sticky top-0 z-50 border-b border-neutral-200 bg-white/80 backdrop-blur-lg dark:border-neutral-800 dark:bg-neutral-900/80">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
                <div className="flex h-16 items-center justify-between">
                    {/* Logo */}
                    <div className="flex items-center">
                        <Link href="/" className="flex items-center gap-2">
                            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600">
                                <FolderOpenIcon className="h-5 w-5 text-white" />
                            </div>
                            <span className="text-lg font-semibold text-neutral-900 dark:text-white">
                                RAG Explorer
                            </span>
                        </Link>
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
