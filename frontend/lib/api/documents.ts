/**
 * API client for IntelliFile backend
 */

import type {
  DocumentMetadata,
  DocumentsListResponse,
  DocumentSearchResponse,
  DocumentSummaryResponse,
  DocumentsQueryParams,
  SearchQueryParams,
  RecommendationResponse,
  SimilarDocumentsResponse,
} from "@/lib/types";
import { API_URL } from "@/lib/constants";

/**
 * Generic fetch wrapper with error handling
 */
async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_URL}${endpoint}`;

  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `API Error: ${response.status} ${response.statusText}`
    );
  }

  return response.json();
}

/**
 * Build query string from params object
 */
function buildQueryString<T extends object>(params: T): string {
  const searchParams = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      if (Array.isArray(value)) {
        searchParams.append(key, value.join(","));
      } else {
        searchParams.append(key, String(value));
      }
    }
  });

  const queryString = searchParams.toString();
  return queryString ? `?${queryString}` : "";
}

// ============================================================
// Document Explorer API
// ============================================================

/**
 * Fetch list of documents with pagination and filtering
 */
export async function getDocuments(
  params: DocumentsQueryParams = {}
): Promise<DocumentsListResponse> {
  const queryString = buildQueryString(params);
  return apiFetch<DocumentsListResponse>(`/documents${queryString}`);
}

/**
 * Fetch a single document by ID
 */
export async function getDocument(
  documentId: string
): Promise<DocumentMetadata> {
  return apiFetch<DocumentMetadata>(`/documents/${documentId}`);
}

/**
 * Delete a document by ID
 */
export async function deleteDocument(
  documentId: string
): Promise<{ success: boolean }> {
  return apiFetch<{ success: boolean }>(`/upload/document/${documentId}`, {
    method: "DELETE",
  });
}

// ============================================================
// Search API
// ============================================================

/**
 * Advanced search with filters
 */
export async function searchDocuments(
  params: SearchQueryParams
): Promise<DocumentSearchResponse> {
  const queryString = buildQueryString(params);
  return apiFetch<DocumentSearchResponse>(`/documents/search${queryString}`);
}

/**
 * Fetch available tags from backend
 */
export async function getTags(): Promise<{ success: boolean; tags: string[] }> {
  return apiFetch<{ success: boolean; tags: string[] }>(`/documents/tags`);
}

/**
 * Get document recommendations based on a query
 */
export async function getRecommendations(
  query: string,
  topK: number = 10,
  fileTypes?: string[]
): Promise<RecommendationResponse> {
  const params: Record<string, unknown> = { query, top_k: topK };
  if (fileTypes?.length) {
    params.file_types = fileTypes;
  }
  const queryString = buildQueryString(params);
  return apiFetch<RecommendationResponse>(`/documents/recommend${queryString}`);
}

// ============================================================
// Document Details API
// ============================================================

/**
 * Get smart summary for a document
 */
export async function getDocumentSummary(
  documentId: string,
  forceRegenerate: boolean = false
): Promise<DocumentSummaryResponse> {
  const queryString = forceRegenerate ? "?force_regenerate=true" : "";
  return apiFetch<DocumentSummaryResponse>(
    `/documents/${documentId}/summary${queryString}`
  );
}

/**
 * Find similar documents
 */
export async function getSimilarDocuments(
  documentId: string,
  limit: number = 10
): Promise<SimilarDocumentsResponse> {
  return apiFetch<SimilarDocumentsResponse>(
    `/documents/${documentId}/similar?limit=${limit}`
  );
}

// ============================================================
// Stats API
// ============================================================

/**
 * Get documents overview statistics
 */
export async function getDocumentsOverview(): Promise<{
  success: boolean;
  total_documents: number;
  total_chunks: number;
  file_types: Record<string, number>;
  document_types: Record<string, number>;
  total_size_mb: number;
}> {
  return apiFetch("/documents/stats/overview");
}

// ============================================================
// File Access
// ============================================================

/**
 * Get the URL to view/download a document file in browser
 */
export function getDocumentFileUrl(
  documentId: string,
  inline: boolean = true
): string {
  return `${API_URL}/documents/${documentId}/file?inline=${inline}`;
}

/**
 * Open document file in browser (for viewing PDFs etc.)
 */
export function viewDocumentInBrowser(documentId: string): void {
  const url = getDocumentFileUrl(documentId, true);
  window.open(url, "_blank", "noopener,noreferrer");
}

/**
 * Download document file via browser
 */
export function downloadDocumentFile(documentId: string): void {
  const url = getDocumentFileUrl(documentId, false);
  window.open(url, "_blank", "noopener,noreferrer");
}

/**
 * Open document file with the system's default application (e.g., Adobe Reader, Word)
 * This calls the backend which triggers the OS to open the file locally.
 */
export async function openDocumentFile(
  documentId: string
): Promise<{ success: boolean; message: string; file_path: string }> {
  return apiFetch<{ success: boolean; message: string; file_path: string }>(
    `/documents/${documentId}/open`,
    { method: "POST" }
  );
}

/**
 * Get the local file path for a document
 */
export async function getDocumentPath(documentId: string): Promise<{
  success: boolean;
  file_path: string;
  folder_path: string;
  exists: boolean;
}> {
  return apiFetch(`/documents/${documentId}/path`);
}

/**
 * Copy text to clipboard
 */
export async function copyToClipboard(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    return false;
  }
}

// ============================================================
// Upload API
// ============================================================

/**
 * Upload a document file
 */
export async function uploadDocument(file: File): Promise<{
  success: boolean;
  message: string;
  file_id: string;
  filename: string;
  chunks_created: number;
}> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/upload/document`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "Upload failed");
  }

  return response.json();
}
