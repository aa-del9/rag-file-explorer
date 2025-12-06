'use client';

/**
 * ServerStatusBanner component
 * Checks if the backend server is running and displays a warning if not
 */

import { useEffect, useState } from 'react';
import { ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { API_URL } from '@/lib/constants';
import Link from 'next/link';

type ServerStatus = 'checking' | 'online' | 'offline';

export function ServerStatusBanner() {
    const [status, setStatus] = useState<ServerStatus>('checking');
    const [dismissed, setDismissed] = useState(false);

    useEffect(() => {
        const checkHealth = async () => {
            try {
                const response = await fetch(`${API_URL}/health`, {
                    method: 'GET',
                    // Short timeout to avoid long waits
                    signal: AbortSignal.timeout(5000),
                });

                if (response.ok) {
                    setStatus('online');
                } else {
                    setStatus('offline');
                }
            } catch {
                setStatus('offline');
            }
        };

        checkHealth();

        // Re-check every 30 seconds
        const interval = setInterval(checkHealth, 30000);
        return () => clearInterval(interval);
    }, []);

    // Don't show anything if online or dismissed
    if (status === 'online' || dismissed) {
        return null;
    }

    // Show loading state briefly
    if (status === 'checking') {
        return null;
    }

    return (
        <div className="bg-amber-50 border-b border-amber-200 dark:bg-amber-900/20 dark:border-amber-800">
            <div className="mx-auto max-w-7xl px-4 py-3 sm:px-6 lg:px-8">
                <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                        <div className="flex-shrink-0">
                            <ExclamationTriangleIcon className="h-5 w-5 text-amber-600 dark:text-amber-400" />
                        </div>
                        <div className="flex-1">
                            <p className="text-sm font-medium text-amber-800 dark:text-amber-200">
                                Backend server is not running
                            </p>
                            <p className="text-sm text-amber-700 dark:text-amber-300">
                                Start the server at <code className="rounded bg-amber-100 px-1.5 py-0.5 font-mono text-xs dark:bg-amber-900/50">localhost:8000</code> to use IntelliFile features.
                                More info <Link
                                    href="https://github.com/aa-del9/rag-file-explorer/tree/main/backend#%EF%B8%8F-installation"
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="underline hover:text-amber-900 dark:hover:text-amber-100"
                                >
                                    here
                                </Link>
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={() => setDismissed(true)}
                        className="flex-shrink-0 rounded-md p-1 text-amber-600 hover:bg-amber-100 hover:text-amber-800 dark:text-amber-400 dark:hover:bg-amber-900/50 dark:hover:text-amber-200"
                        aria-label="Dismiss"
                    >
                        <XMarkIcon className="h-5 w-5" />
                    </button>
                </div>
            </div>
        </div>
    );
}
