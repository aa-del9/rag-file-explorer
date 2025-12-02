'use client';

/**
 * Document Detail Page
 * Shows detailed information about a single document
 */

import { useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useDocument, useDocumentSummary, useSimilarDocuments } from '@/lib/hooks';
import { FileTypeIcon, FileTypeBadge, DocumentCard } from '@/components/documents';
import { openDocumentFile, viewDocumentInBrowser, copyToClipboard } from '@/lib/api';
import {
    ArrowLeftIcon,
    CalendarIcon,
    DocumentTextIcon,
    UserIcon,
    TagIcon,
    SparklesIcon,
    ClockIcon,
    FolderIcon,
    FolderOpenIcon,
    ArrowTopRightOnSquareIcon,
    ClipboardDocumentIcon,
    CheckIcon,
} from '@heroicons/react/24/outline';

function formatDate(dateString: string): string {
    if (!dateString) return 'Unknown';
    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    } catch {
        return dateString;
    }
}

function formatFileSize(sizeInMb: number): string {
    if (sizeInMb < 1) {
        return `${(sizeInMb * 1024).toFixed(0)} KB`;
    }
    return `${sizeInMb.toFixed(2)} MB`;
}

export default function DocumentDetailPage() {
    const params = useParams();
    const router = useRouter();
    const documentId = params.id as string;

    // UI state
    const [isOpening, setIsOpening] = useState(false);
    const [copied, setCopied] = useState(false);

    // Fetch document details
    const {
        data: document,
        isLoading: isLoadingDoc,
        isError: isDocError,
        error: docError,
    } = useDocument(documentId);

    // Fetch AI summary
    const {
        data: summaryData,
        isLoading: isLoadingSummary,
    } = useDocumentSummary(documentId);

    // Fetch similar documents
    const {
        data: similarData,
        isLoading: isLoadingSimilar,
    } = useSimilarDocuments(documentId, 4);

    // Handler to open file with system application
    const handleOpenFile = async () => {
        setIsOpening(true);
        try {
            await openDocumentFile(documentId);
        } catch (error) {
            console.error('Failed to open file:', error);
        } finally {
            setIsOpening(false);
        }
    };

    // Handler to copy file path
    const handleCopyPath = async () => {
        if (document?.file_path) {
            const success = await copyToClipboard(document.file_path);
            if (success) {
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
            }
        }
    };

    if (isLoadingDoc) {
        return (
            <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
                <div className="animate-pulse space-y-6">
                    <div className="h-8 w-48 rounded bg-neutral-200 dark:bg-neutral-700" />
                    <div className="h-64 rounded-lg bg-neutral-200 dark:bg-neutral-700" />
                    <div className="h-48 rounded-lg bg-neutral-200 dark:bg-neutral-700" />
                </div>
            </div>
        );
    }

    if (isDocError || !document) {
        return (
            <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
                <div className="text-center">
                    <h1 className="text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                        Document Not Found
                    </h1>
                    <p className="mt-2 text-neutral-600 dark:text-neutral-400">
                        {docError?.message || 'The document you are looking for does not exist.'}
                    </p>
                    <Link
                        href="/explorer"
                        className="mt-4 inline-flex items-center gap-2 text-blue-600 hover:text-blue-700 dark:text-blue-400"
                    >
                        <ArrowLeftIcon className="h-4 w-4" />
                        Back to Explorer
                    </Link>
                </div>
            </div>
        );
    }

    return (
        <div className="mx-auto max-w-4xl px-4 py-8 sm:px-6 lg:px-8">
            {/* Back Button */}
            <Link
                href="/explorer"
                className="mb-6 inline-flex items-center gap-2 text-sm text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-neutral-100"
            >
                <ArrowLeftIcon className="h-4 w-4" />
                Back to Explorer
            </Link>

            {/* Document Header */}
            <div className="rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
                <div className="flex items-start gap-4">
                    <FileTypeIcon fileType={document.file_type} size="lg" />
                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3">
                            <h1 className="truncate text-2xl font-bold text-neutral-900 dark:text-neutral-100">
                                {document.display_name}
                            </h1>
                            <FileTypeBadge fileType={document.file_type} />
                        </div>

                        {document.title && document.title !== document.display_name && (
                            <p className="mt-1 text-lg text-neutral-600 dark:text-neutral-400">
                                {document.title}
                            </p>
                        )}

                        {/* Metadata Grid */}
                        <div className="mt-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
                            <div className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
                                <CalendarIcon className="h-4 w-4" />
                                <span>Created: {formatDate(document.created_at)}</span>
                            </div>

                            {document.page_count && (
                                <div className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
                                    <DocumentTextIcon className="h-4 w-4" />
                                    <span>{document.page_count} pages</span>
                                </div>
                            )}

                            <div className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
                                <ClockIcon className="h-4 w-4" />
                                <span>{formatFileSize(document.file_size_mb)}</span>
                            </div>

                            {document.author && (
                                <div className="flex items-center gap-2 text-sm text-neutral-600 dark:text-neutral-400">
                                    <UserIcon className="h-4 w-4" />
                                    <span>{document.author}</span>
                                </div>
                            )}
                        </div>

                        {/* Keywords/Tags */}
                        {(document.ai_keywords?.length || document.tags?.length) && (
                            <div className="mt-4 flex flex-wrap gap-2">
                                {document.ai_keywords?.map((keyword) => (
                                    <span
                                        key={keyword}
                                        className="inline-flex items-center gap-1 rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                                    >
                                        <TagIcon className="h-3 w-3" />
                                        {keyword}
                                    </span>
                                ))}
                                {document.tags?.map((tag) => (
                                    <span
                                        key={tag}
                                        className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400"
                                    >
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        )}

                        {/* File Path */}
                        {document.file_path && (
                            <div className="mt-4 flex items-center gap-2 rounded-lg bg-neutral-50 px-3 py-2 dark:bg-neutral-800">
                                <FolderIcon className="h-4 w-4 flex-shrink-0 text-neutral-500" />
                                <span className="flex-1 truncate font-mono text-xs text-neutral-600 dark:text-neutral-400" title={document.file_path}>
                                    {document.file_path}
                                </span>
                                <button
                                    onClick={handleCopyPath}
                                    className="flex-shrink-0 rounded p-1 text-neutral-500 hover:bg-neutral-200 hover:text-neutral-700 dark:hover:bg-neutral-700 dark:hover:text-neutral-300"
                                    title="Copy path to clipboard"
                                >
                                    {copied ? (
                                        <CheckIcon className="h-4 w-4 text-green-500" />
                                    ) : (
                                        <ClipboardDocumentIcon className="h-4 w-4" />
                                    )}
                                </button>
                            </div>
                        )}

                        {/* Action Buttons */}
                        <div className="mt-4 flex flex-wrap gap-2">
                            <button
                                onClick={handleOpenFile}
                                disabled={isOpening}
                                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
                            >
                                <FolderOpenIcon className="h-4 w-4" />
                                {isOpening ? 'Opening...' : 'Open with App'}
                            </button>
                            <button
                                onClick={() => viewDocumentInBrowser(document.document_id)}
                                className="inline-flex items-center gap-2 rounded-lg border border-neutral-300 bg-white px-4 py-2 text-sm font-medium text-neutral-700 hover:bg-neutral-50 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-300 dark:hover:bg-neutral-700 transition-colors"
                            >
                                <ArrowTopRightOnSquareIcon className="h-4 w-4" />
                                Download
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            {/* AI Summary Section */}
            <div className="mt-6 rounded-lg border border-neutral-200 bg-white p-6 dark:border-neutral-800 dark:bg-neutral-900">
                <div className="flex items-center gap-2 mb-4">
                    <SparklesIcon className="h-5 w-5 text-purple-500" />
                    <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                        AI Summary
                    </h2>
                    {summaryData?.cached && (
                        <span className="rounded-full bg-neutral-100 px-2 py-0.5 text-xs text-neutral-500 dark:bg-neutral-800">
                            Cached
                        </span>
                    )}
                </div>

                {isLoadingSummary ? (
                    <div className="animate-pulse space-y-2">
                        <div className="h-4 w-full rounded bg-neutral-200 dark:bg-neutral-700" />
                        <div className="h-4 w-5/6 rounded bg-neutral-200 dark:bg-neutral-700" />
                        <div className="h-4 w-4/6 rounded bg-neutral-200 dark:bg-neutral-700" />
                    </div>
                ) : summaryData ? (
                    <div className="space-y-4">
                        <p className="text-neutral-700 dark:text-neutral-300 leading-relaxed">
                            {summaryData.summary}
                        </p>

                        {(summaryData.key_topics?.length ?? 0) > 0 && (
                            <div>
                                <h3 className="text-sm font-medium text-neutral-600 dark:text-neutral-400 mb-2">
                                    Key Topics
                                </h3>
                                <div className="flex flex-wrap gap-2">
                                    {summaryData.key_topics?.map((topic) => (
                                        <span
                                            key={topic}
                                            className="rounded-full bg-purple-100 px-3 py-1 text-sm text-purple-700 dark:bg-purple-900/30 dark:text-purple-400"
                                        >
                                            {topic}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <p className="text-neutral-500 dark:text-neutral-400">
                        {document.ai_summary || 'No summary available for this document.'}
                    </p>
                )}
            </div>

            {/* Similar Documents Section */}
            <div className="mt-6">
                <h2 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
                    Similar Documents
                </h2>

                {isLoadingSimilar ? (
                    <div className="grid gap-4 sm:grid-cols-2">
                        {[1, 2, 3, 4].map((i) => (
                            <div
                                key={i}
                                className="animate-pulse h-32 rounded-lg bg-neutral-200 dark:bg-neutral-700"
                            />
                        ))}
                    </div>
                ) : similarData?.similar_documents?.length ? (
                    <div className="grid gap-4 sm:grid-cols-2">
                        {similarData.similar_documents.map((doc) => (
                            <DocumentCard key={doc.document_id} document={doc} variant="list" />
                        ))}
                    </div>
                ) : (
                    <p className="text-neutral-500 dark:text-neutral-400">
                        No similar documents found.
                    </p>
                )}
            </div>
        </div>
    );
}
