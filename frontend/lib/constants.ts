/**
 * Document sorting options
 */
export type SortOption = {
  label: string;
  value: string;
  sortBy: 'name' | 'created_at' | 'file_size' | 'relevance';
  order: 'asc' | 'desc';
};

export const defaultSort: SortOption = {
  label: 'Relevance',
  value: 'relevance',
  sortBy: 'relevance',
  order: 'desc',
};

export const sortOptions: SortOption[] = [
  defaultSort,
  { label: 'Name (A-Z)', value: 'name-asc', sortBy: 'name', order: 'asc' },
  { label: 'Name (Z-A)', value: 'name-desc', sortBy: 'name', order: 'desc' },
  { label: 'Newest first', value: 'date-desc', sortBy: 'created_at', order: 'desc' },
  { label: 'Oldest first', value: 'date-asc', sortBy: 'created_at', order: 'asc' },
  { label: 'Size (largest)', value: 'size-desc', sortBy: 'file_size', order: 'desc' },
  { label: 'Size (smallest)', value: 'size-asc', sortBy: 'file_size', order: 'asc' },
];

/**
 * File type categories for filtering
 */
export const FILE_TYPE_CATEGORIES = {
  documents: ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'],
  spreadsheets: ['xls', 'xlsx', 'csv', 'ods'],
  presentations: ['ppt', 'pptx', 'odp'],
  images: ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'],
  code: ['js', 'ts', 'py', 'java', 'cpp', 'c', 'html', 'css', 'json', 'xml'],
  archives: ['zip', 'rar', '7z', 'tar', 'gz'],
};

/**
 * TanStack Query keys
 */
export const QUERY_KEYS = {
  documents: 'documents',
  document: 'document',
  search: 'search',
  recommendations: 'recommendations',
  similar: 'similar',
  summary: 'summary',
} as const;

/**
 * API configuration
 */
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Pagination defaults
 */
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_PAGE_SIZE = 100;

