import { GeistSans } from 'geist/font/sans';
import { ReactNode } from 'react';
import { Toaster } from 'sonner';
import './globals.css';
import { Navbar } from '@/components/layout/navbar';
// import { Footer } from '@/components/layout/footer-new';
import { QueryProvider } from '@/lib/providers';

const SITE_NAME = 'RAG File Explorer';

export const metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL || 'http://localhost:3000'),
  title: {
    default: SITE_NAME,
    template: `%s | ${SITE_NAME}`
  },
  description: 'Intelligent document search and exploration powered by AI',
  robots: {
    follow: true,
    index: true
  }
};

export default function RootLayout({
  children
}: {
  children: ReactNode;
}) {
  return (
    <html lang="en" className={GeistSans.variable}>
      <body className="flex min-h-screen flex-col bg-neutral-50 text-black selection:bg-blue-300 dark:bg-neutral-900 dark:text-white dark:selection:bg-blue-500 dark:selection:text-white">
        <QueryProvider>
          <Navbar />
          <main className="flex-1">
            {children}
          </main>
          {/* <Footer /> */}
          <Toaster closeButton />
        </QueryProvider>
      </body>
    </html>
  );
}
