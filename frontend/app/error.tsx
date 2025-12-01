'use client';

export default function Error({ reset }: { reset: () => void }) {
  return (
    <div className="mx-auto my-4 flex max-w-xl flex-col rounded-lg border border-neutral-200 bg-white p-8 md:p-12 dark:border-neutral-800 dark:bg-neutral-900">
      <h2 className="text-xl font-bold text-neutral-900 dark:text-neutral-100">
        Something went wrong
      </h2>
      <p className="my-2 text-neutral-600 dark:text-neutral-400">
        There was an issue loading this page. This could be a temporary issue, please try again.
      </p>
      <button
        className="mx-auto mt-4 flex w-full items-center justify-center rounded-full bg-blue-600 p-4 tracking-wide text-white hover:bg-blue-700"
        onClick={() => reset()}
      >
        Try Again
      </button>
    </div>
  );
}
