/**
 * Footer component
 */

export function Footer() {
  return (
    <footer className="border-t border-neutral-200 bg-white dark:border-neutral-800 dark:bg-neutral-900">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <p className="text-sm text-neutral-500 dark:text-neutral-400">
            IntelliFile — Intelligent document search powered by AI
          </p>
          <p className="text-sm text-neutral-400 dark:text-neutral-500">
            Built with Next.js and LLama 3.1
          </p>
        </div>
      </div>
    </footer>
  );
}
