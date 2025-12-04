/**
 * Document types for IntelliFile
 */

export interface DocumentMetadata {
  document_id: string;
  filename: string;
  display_name: string; // Filename without UUID prefix
  file_path: string;
  file_size_mb: number;
  file_type: string;
  page_count: number | null;
  created_at: string;
  modified_at: string;
  title: string | null;
  author: string | null;
  ai_summary: string | null;
  ai_keywords: string[] | null;
  ai_document_type: string | null;
  similarity_score: number | null;
  preview_snippet: string | null;
  tags: string[] | null;
}

export interface DocumentSearchResult extends DocumentMetadata {
  document_score: number | null;
  chunk_score: number | null;
  aggregated_score: number | null;
  relevant_chunks: ChunkRelevance[] | null;
}

export interface ChunkRelevance {
  chunk_id: string;
  text: string;
  similarity_score: number;
  chunk_index: number | null;
}

export interface DocumentsListResponse {
  success: boolean;
  total_documents: number;
  page: number;
  page_size: number;
  total_pages: number;
  documents: DocumentMetadata[];
}

export interface DocumentSearchResponse {
  success: boolean;
  total_results: number;
  documents: DocumentSearchResult[];
  query_params: Record<string, unknown>;
  search_type: "semantic" | "metadata" | "hybrid";
  processing_time_ms: number | null;
}

export interface RecommendationResponse {
  success: boolean;
  query: string;
  total_results: number;
  recommendations: DocumentSearchResult[];
}

export interface SimilarDocumentsResponse {
  success: boolean;
  source_document_id: string;
  source_document_filename: string;
  total_results: number;
  similar_documents: DocumentSearchResult[];
}

export interface DocumentSummaryResponse {
  success: boolean;
  document_id: string;
  filename: string;
  summary: string;
  key_topics: string[] | null;
  metadata_summary: {
    file_info: {
      type: string;
      size_mb: number;
      page_count: number | null;
    };
    dates: {
      created: string;
      modified: string;
    };
    authorship: {
      title: string | null;
      author: string | null;
    };
    classification: {
      document_type: string | null;
      keywords: string | null;
    };
  };
  cached: boolean;
  generated_at: string;
}

// Filter and sorting types
export type SortField =
  | "filename"
  | "created_at"
  | "modified_at"
  | "file_size_mb"
  | "page_count";
export type SortOrder = "asc" | "desc";

export interface DocumentFilters {
  filename_contains?: string;
  file_types?: string[];
  document_types?: string[];
  authors?: string[];
  tags?: string[];
  min_pages?: number;
  max_pages?: number;
  min_size_mb?: number;
  max_size_mb?: number;
  created_after?: string;
  created_before?: string;
}

export interface DocumentsQueryParams {
  page?: number;
  page_size?: number;
  sort_by?: SortField;
  sort_order?: SortOrder;
  file_type?: string;
  filename_contains?: string;
}

export interface SearchQueryParams extends DocumentFilters {
  query?: string;
  top_k?: number;
  include_chunk_scores?: boolean;
  sort_by?: SortField;
  sort_order?: SortOrder;
}
