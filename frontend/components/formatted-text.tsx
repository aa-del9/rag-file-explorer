'use client';

/**
 * FormattedText component
 * Renders text with basic markdown-like formatting
 * Supports: **bold**, headings, numbered lists
 */

import clsx from 'clsx';

interface FormattedTextProps {
    text: string;
    className?: string;
}

/**
 * Parse and render formatted text
 * Supports:
 * - **text** for bold/headings
 * - Numbered lists (1. 2. 3.)
 * - Line breaks
 */
export function FormattedText({ text, className }: FormattedTextProps) {
    if (!text) return null;

    // Split by double asterisks to find bold sections
    const parts = text.split(/(\*\*[^*]+\*\*)/g);

    const rendered = parts.map((part, index) => {
        // Check if this is a bold section
        if (part.startsWith('**') && part.endsWith('**')) {
            const content = part.slice(2, -2);

            // Check if it's a heading pattern like "SUMMARY:" or "KEY_TOPICS:"
            if (content.match(/^[A-Z_]+:$/)) {
                return (
                    <span key={index} className="block mt-4 first:mt-0 mb-2 text-base font-semibold text-neutral-900 dark:text-white">
                        {content.replace('_', ' ')}
                    </span>
                );
            }

            // Check if it's a numbered item heading like "1. Database Schema Design"
            if (content.match(/^\d+\.\s+/)) {
                return (
                    <span key={index} className="font-semibold text-neutral-800 dark:text-neutral-200">
                        {content}
                    </span>
                );
            }

            // Regular bold text
            return (
                <strong key={index} className="font-semibold text-neutral-800 dark:text-neutral-200">
                    {content}
                </strong>
            );
        }

        // Regular text - handle line breaks and clean up
        return (
            <span key={index}>
                {part.split('\n').map((line, lineIndex, arr) => (
                    <span key={lineIndex}>
                        {line}
                        {lineIndex < arr.length - 1 && <br />}
                    </span>
                ))}
            </span>
        );
    });

    return (
        <div className={clsx('text-neutral-700 dark:text-neutral-300 leading-relaxed', className)}>
            {rendered}
        </div>
    );
}

/**
 * More structured markdown renderer for AI summaries
 * Parses the specific format: **HEADING:** content
 */
export function AISummaryText({ text, className }: FormattedTextProps) {
    if (!text) return null;

    // Split into sections based on **HEADING:** pattern
    const sections: { heading?: string; content: string }[] = [];

    // Match pattern like **SUMMARY:** or **KEY_TOPICS:**
    const headingPattern = /\*\*([A-Z_]+):\*\*/g;
    let lastIndex = 0;
    let match;

    while ((match = headingPattern.exec(text)) !== null) {
        // Add any content before this heading
        if (match.index > lastIndex) {
            const beforeContent = text.slice(lastIndex, match.index).trim();
            if (beforeContent) {
                sections.push({ content: beforeContent });
            }
        }

        // Find the end of this section (next heading or end of text)
        const headingEnd = match.index + match[0].length;
        const nextMatch = headingPattern.exec(text);
        headingPattern.lastIndex = headingEnd; // Reset to continue from current position

        const contentEnd = nextMatch ? nextMatch.index : text.length;
        const content = text.slice(headingEnd, contentEnd).trim();

        sections.push({
            heading: (match[1] ?? '').replace(/_/g, ' '),
            content,
        });

        lastIndex = contentEnd;

        // Reset for next iteration if there was a next match
        if (nextMatch) {
            headingPattern.lastIndex = nextMatch.index;
        }
    }

    // Add any remaining content
    if (lastIndex < text.length) {
        const remaining = text.slice(lastIndex).trim();
        if (remaining) {
            sections.push({ content: remaining });
        }
    }

    // If no sections were found, parse the whole text
    if (sections.length === 0) {
        sections.push({ content: text });
    }

    return (
        <div className={clsx('space-y-4', className)}>
            {sections.map((section, index) => (
                <div key={index}>
                    {section.heading && (
                        <h4 className="text-sm font-semibold text-neutral-900 dark:text-white mb-2 uppercase tracking-wide">
                            {section.heading}
                        </h4>
                    )}
                    <div className="text-neutral-700 dark:text-neutral-300 leading-relaxed">
                        <FormattedContent text={section.content} />
                    </div>
                </div>
            ))}
        </div>
    );
}

/**
 * Format content within a section
 * Handles numbered lists and bold text
 */
function FormattedContent({ text }: { text: string }) {
    // Check if this looks like a numbered list
    const numberedListPattern = /(\d+)\.\s+\*\*([^*]+)\*\*:\s*/g;

    if (numberedListPattern.test(text)) {
        // Reset pattern
        numberedListPattern.lastIndex = 0;

        // Split into list items
        const items: { number: string; title: string; description: string }[] = [];
        let match;

        while ((match = numberedListPattern.exec(text)) !== null) {
            const number = match[1] ?? '';
            const title = match[2] ?? '';

            if (!number || !title) continue;

            // Find where this item ends (next number or end)
            const nextPattern = new RegExp(`${parseInt(number) + 1}\\.\\s+\\*\\*`);
            const nextMatch = text.slice(match.index + match[0].length).match(nextPattern);

            const descEnd = nextMatch && nextMatch.index !== undefined
                ? match.index + match[0].length + nextMatch.index
                : text.length;

            const description = text.slice(match.index + match[0].length, descEnd).trim();

            items.push({ number, title, description });
        }

        if (items.length > 0) {
            return (
                <ol className="list-none space-y-3 mt-2">
                    {items.map((item, index) => (
                        <li key={index} className="flex gap-3">
                            <span className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-blue-100 text-blue-700 text-xs font-medium dark:bg-blue-900/30 dark:text-blue-400">
                                {item.number}
                            </span>
                            <div>
                                <span className="font-medium text-neutral-800 dark:text-neutral-200">
                                    {item.title}
                                </span>
                                {item.description && (
                                    <span className="text-neutral-600 dark:text-neutral-400">
                                        : {item.description}
                                    </span>
                                )}
                            </div>
                        </li>
                    ))}
                </ol>
            );
        }
    }

    // Otherwise, render with simple bold formatting
    const parts = text.split(/(\*\*[^*]+\*\*)/g);

    return (
        <>
            {parts.map((part, index) => {
                if (part.startsWith('**') && part.endsWith('**')) {
                    return (
                        <strong key={index} className="font-medium text-neutral-800 dark:text-neutral-200">
                            {part.slice(2, -2)}
                        </strong>
                    );
                }
                return <span key={index}>{part}</span>;
            })}
        </>
    );
}
