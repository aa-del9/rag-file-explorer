import { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'Upload Documents | IntelliFile',
    description: 'Upload PDF, DOC, and DOCX files to IntelliFile. AI-powered document processing with automatic metadata extraction.',
};

export default function UploadLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return children;
}
