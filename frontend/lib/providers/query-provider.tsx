'use client';

/**
 * TanStack Query Provider for the application
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ReactNode, useState } from 'react';

export function QueryProvider({ children }: { children: ReactNode }) {
    const [queryClient] = useState(
        () =>
            new QueryClient({
                defaultOptions: {
                    queries: {
                        // Stale time: 5 minutes
                        staleTime: 5 * 60 * 1000,
                        // Cache time: 30 minutes
                        gcTime: 30 * 60 * 1000,
                        // Retry failed requests 3 times
                        retry: 3,
                        // Refetch on window focus
                        refetchOnWindowFocus: false,
                    },
                },
            })
    );

    return (
        <QueryClientProvider client={queryClient}>
            {children}
            <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
    );
}
