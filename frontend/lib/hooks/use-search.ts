"use client";

import { useState, useMemo, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { searchDocuments, getTags } from "@/lib/api";
import { useDebounce } from "./use-debounce";
import type {
  DocumentFilters,
  SearchQueryParams,
  DocumentSearchResponse,
} from "@/lib/types";

const SEARCH_KEY = ["documents", "search"] as const;
const TAGS_KEY = ["documents", "tags"] as const;

export function useSearchManager(initialFilters: DocumentFilters = {}) {
  const [query, setQuery] = useState<string>("");
  const [filters, setFilters] = useState<DocumentFilters>(initialFilters);
  const [sortBy, setSortBy] = useState<string | undefined>(undefined);
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(20);

  const debouncedQuery = useDebounce(query, 300);

  const params: SearchQueryParams = useMemo(() => {
    const p: SearchQueryParams = {
      ...filters,
      query: debouncedQuery || undefined,
      top_k: 50,
      include_chunk_scores: false,
    };

    if (sortBy) p.sort_by = sortBy as any;
    if (sortOrder) p.sort_order = sortOrder as any;

    return p;
  }, [filters, debouncedQuery, sortBy, sortOrder]);

  const { data, isLoading, isError, error, refetch, isFetching } =
    useQuery<DocumentSearchResponse>({
      queryKey: [...SEARCH_KEY, params, page, pageSize],
      queryFn: () => searchDocuments(params),
      enabled: !!(debouncedQuery || Object.keys(filters).length > 0),
      placeholderData: (previousData) => previousData,
    });

  const tagsQuery = useQuery({
    queryKey: TAGS_KEY,
    queryFn: getTags,
  });

  const setFilter = useCallback((partial: Partial<DocumentFilters>) => {
    setFilters((prev) => ({ ...prev, ...partial }));
    setPage(1);
  }, []);

  const resetFilters = useCallback(() => {
    setFilters({});
    setPage(1);
  }, []);

  return {
    // state
    query,
    setQuery,
    debouncedQuery,
    filters,
    setFilters: setFilter,
    resetFilters,
    sortBy,
    setSortBy,
    sortOrder,
    setSortOrder,
    page,
    setPage,
    pageSize,
    setPageSize,

    // results
    results: data,
    isLoading,
    isFetching,
    isError,
    error,
    refetch,

    // tags
    tagsData: tagsQuery.data,
    tagsLoading: tagsQuery.isLoading,
  } as const;
}
