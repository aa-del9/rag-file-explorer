import { Metadata } from 'next';

export const metadata: Metadata = {
    title: 'Explorer | IntelliFile',
    description: 'Browse and search your documents with AI-powered insights',
};

export default function ExplorerLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return <>{children}</>;
}
