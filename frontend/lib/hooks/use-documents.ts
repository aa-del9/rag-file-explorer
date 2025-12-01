'use client';

/**
 * Custom hook for fetching and managing documents
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getDocuments,
  getDocument,
  deleteDocument,
  searchDocuments,
  getRecommendations,
  getDocumentSummary,
  getSimilarDocuments,
  getDocumentsOverview,
  uploadDocument,
} from '@/lib/api';
import type {
  DocumentsQueryParams,
  SearchQueryParams,
} from '@/lib/types';

// Query keys for cache management
export const documentKeys = {
  all: ['documents'] as const,
  lists: () => [...documentKeys.all, 'list'] as const,
  list: (params: DocumentsQueryParams) => [...documentKeys.lists(), params] as const,
  details: () => [...documentKeys.all, 'detail'] as const,
  detail: (id: string) => [...documentKeys.details(), id] as const,
  summaries: () => [...documentKeys.all, 'summary'] as const,
  summary: (id: string) => [...documentKeys.summaries(), id] as const,
  similar: (id: string) => [...documentKeys.all, 'similar', id] as const,
  search: (params: SearchQueryParams) => [...documentKeys.all, 'search', params] as const,
  recommendations: (query: string) => [...documentKeys.all, 'recommendations', query] as const,
  overview: () => [...documentKeys.all, 'overview'] as const,
};

/**
 * Hook to fetch list of documents with pagination
 */
export function useDocuments(params: DocumentsQueryParams = {}) {
  return useQuery({
    queryKey: documentKeys.list(params),
    queryFn: () => getDocuments(params),
  });
}

/**
 * Hook to fetch a single document by ID
 */
export function useDocument(documentId: string | null) {
  return useQuery({
    queryKey: documentKeys.detail(documentId || ''),
    queryFn: () => getDocument(documentId!),
    enabled: !!documentId,
  });
}

/**
 * Hook to search documents
 */
export function useSearchDocuments(params: SearchQueryParams) {
  return useQuery({
    queryKey: documentKeys.search(params),
    queryFn: () => searchDocuments(params),
    enabled: !!(params.query || Object.keys(params).length > 0),
  });
}

/**
 * Hook to get document recommendations
 */
export function useRecommendations(
  query: string,
  topK: number = 10,
  fileTypes?: string[]
) {
  return useQuery({
    queryKey: documentKeys.recommendations(query),
    queryFn: () => getRecommendations(query, topK, fileTypes),
    enabled: !!query,
  });
}

/**
 * Hook to get document summary
 */
export function useDocumentSummary(documentId: string | null) {
  return useQuery({
    queryKey: documentKeys.summary(documentId || ''),
    queryFn: () => getDocumentSummary(documentId!),
    enabled: !!documentId,
  });
}

/**
 * Hook to get similar documents
 */
export function useSimilarDocuments(documentId: string | null, limit: number = 10) {
  return useQuery({
    queryKey: documentKeys.similar(documentId || ''),
    queryFn: () => getSimilarDocuments(documentId!, limit),
    enabled: !!documentId,
  });
}

/**
 * Hook to get documents overview statistics
 */
export function useDocumentsOverview() {
  return useQuery({
    queryKey: documentKeys.overview(),
    queryFn: getDocumentsOverview,
  });
}

/**
 * Hook to upload a document
 */
export function useUploadDocument() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      // Invalidate all document queries to refetch
      queryClient.invalidateQueries({ queryKey: documentKeys.all });
    },
  });
}

/**
 * Hook to delete a document
 */
export function useDeleteDocument() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      // Invalidate all document queries to refetch
      queryClient.invalidateQueries({ queryKey: documentKeys.all });
    },
  });
}
