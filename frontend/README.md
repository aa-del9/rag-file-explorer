# IntelliFile - Frontend

A modern, intelligent document explorer built with Next.js 15, React 19, and TanStack Query. This frontend connects to the IntelliFile backend to provide semantic search, document browsing, and AI-powered document insights.

## Features

- **📂 IntelliFile Explorer** - Browse and manage your documents with grid/list views
- **🔍 Global Search** - Semantic search powered by AI embeddings
- **🎛️ Advanced Filters** - Filter by file type, date range, page count, file size, and tags
- **📊 Sorting Controls** - Sort by name, date, size, page count, or relevance
- **📄 Document Details** - View AI-generated summaries, keywords, and similar documents
- **🚀 Open with System App** - Open documents directly in their default application (PDF Reader, Word, etc.)
- **📋 Copy File Path** - Quick copy file paths to clipboard
- **🌙 Dark Mode** - Full dark mode support

## Tech Stack

- **Framework**: [Next.js 15](https://nextjs.org/) with App Router
- **React**: React 19 with Server Components
- **State Management**: [TanStack Query](https://tanstack.com/query) for server state
- **Styling**: [Tailwind CSS 4](https://tailwindcss.com/)
- **UI Components**: [Headless UI](https://headlessui.com/), [Heroicons](https://heroicons.com/)
- **Font**: [Geist](https://vercel.com/font)
- **Package Manager**: pnpm

## Project Structure

```
frontend/
├── app/                    # Next.js App Router pages
│   ├── page.tsx           # Home page
│   ├── explorer/          # Document explorer
│   │   ├── page.tsx       # Main explorer view with filters
│   │   └── [id]/          # Document detail page
│   └── search/            # Search results page
├── components/
│   ├── documents/         # Document-related components
│   │   ├── document-card.tsx
│   │   ├── document-list.tsx
│   │   ├── filters-panel.tsx
│   │   ├── sorting-controls.tsx
│   │   └── file-type-icon.tsx
│   └── layout/            # Layout components
│       ├── navbar.tsx
│       └── footer.tsx
├── lib/
│   ├── api/               # API client functions
│   │   └── documents.ts   # Document API calls
│   ├── hooks/             # Custom React hooks
│   │   ├── use-documents.ts
│   │   ├── use-search.ts
│   │   └── use-debounce.ts
│   ├── providers/         # React context providers
│   │   └── query-provider.tsx
│   ├── types/             # TypeScript type definitions
│   │   └── document.ts
│   ├── constants.ts       # App constants
│   └── utils.ts           # Utility functions
└── fonts/                 # Custom fonts
```

## Getting Started

### Prerequisites

- Node.js 18.17 or later
- pnpm (recommended) or npm
- Backend server running (see backend README)

### Environment Setup

1. Copy the environment example file:

```bash
cp .env.example .env.local
```

2. Configure the environment variables:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Installation

```bash
# Install dependencies
pnpm install

# Run development server with Turbopack
pnpm dev
```

Your app should now be running on [http://localhost:3000](http://localhost:3000).

### Build for Production

```bash
# Build the application
pnpm build

# Start production server
pnpm start
```

## API Integration

The frontend connects to the IntelliFile backend API. Key endpoints used:

| Endpoint                      | Description                     |
| ----------------------------- | ------------------------------- |
| `GET /documents`              | List documents with pagination  |
| `GET /documents/search`       | Advanced search with filters    |
| `GET /documents/{id}`         | Get document details            |
| `GET /documents/{id}/summary` | Get AI-generated summary        |
| `GET /documents/{id}/similar` | Find similar documents          |
| `POST /documents/{id}/open`   | Open file in system application |
| `GET /documents/tags`         | List all available tags         |

## Scripts

| Command               | Description                             |
| --------------------- | --------------------------------------- |
| `pnpm dev`            | Start development server with Turbopack |
| `pnpm build`          | Build for production                    |
| `pnpm start`          | Start production server                 |
| `pnpm prettier`       | Format code with Prettier               |
| `pnpm prettier:check` | Check code formatting                   |
