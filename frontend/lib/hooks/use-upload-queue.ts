/**
 * Upload Queue Hook for IntelliFile
 * Manages sequential file uploads with status tracking
 */

import { useState, useCallback, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import {
  uploadDocument,
  validateFile,
  type UploadResponse,
} from "@/lib/api/upload";

/**
 * Upload status for each file in the queue
 */
export type UploadStatus = "pending" | "uploading" | "completed" | "failed";

/**
 * File item in the upload queue
 */
export interface QueuedFile {
  id: string;
  file: File;
  status: UploadStatus;
  progress: number;
  error?: string;
  response?: UploadResponse;
  validationError?: string;
}

/**
 * Hook return type
 */
export interface UseUploadQueueReturn {
  /** Files in the upload queue */
  queue: QueuedFile[];
  /** Add files to the queue */
  addFiles: (files: FileList | File[]) => void;
  /** Remove a file from the queue */
  removeFile: (id: string) => void;
  /** Start uploading all pending files */
  startUpload: () => void;
  /** Clear all completed/failed files */
  clearCompleted: () => void;
  /** Clear entire queue */
  clearAll: () => void;
  /** Retry a failed upload */
  retryFile: (id: string) => void;
  /** Cancel ongoing upload (stops after current file) */
  cancelUpload: () => void;
  /** Is currently uploading */
  isUploading: boolean;
  /** Total files count */
  totalFiles: number;
  /** Completed files count */
  completedFiles: number;
  /** Failed files count */
  failedFiles: number;
  /** Pending files count */
  pendingFiles: number;
}

/**
 * Generate unique ID for queued files
 */
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Upload Queue Hook
 * Manages a queue of files and uploads them sequentially
 */
export function useUploadQueue(): UseUploadQueueReturn {
  const [queue, setQueue] = useState<QueuedFile[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const cancelledRef = useRef(false);
  const isProcessingRef = useRef(false);

  // TanStack Query mutation for single file upload
  const uploadMutation = useMutation({
    mutationFn: uploadDocument,
  });

  /**
   * Update a specific file in the queue
   */
  const updateFile = useCallback((id: string, updates: Partial<QueuedFile>) => {
    setQueue((prev) =>
      prev.map((item) => (item.id === id ? { ...item, ...updates } : item))
    );
  }, []);

  /**
   * Add files to the queue
   */
  const addFiles = useCallback((files: FileList | File[]) => {
    const fileArray = Array.from(files);

    const newItems: QueuedFile[] = fileArray.map((file) => {
      const validation = validateFile(file);
      return {
        id: generateId(),
        file,
        status: validation.isValid ? "pending" : "failed",
        progress: 0,
        validationError: validation.error,
        error: validation.error,
      };
    });

    setQueue((prev) => [...prev, ...newItems]);
  }, []);

  /**
   * Remove a file from the queue
   */
  const removeFile = useCallback((id: string) => {
    setQueue((prev) => prev.filter((item) => item.id !== id));
  }, []);

  /**
   * Process the upload queue sequentially
   */
  const processQueue = useCallback(async () => {
    if (isProcessingRef.current) return;
    isProcessingRef.current = true;
    cancelledRef.current = false;
    setIsUploading(true);

    // Get current queue state
    let currentQueue = queue;

    while (true) {
      // Check if cancelled
      if (cancelledRef.current) break;

      // Find next pending file
      const pendingItem = currentQueue.find(
        (item) => item.status === "pending" && !item.validationError
      );

      if (!pendingItem) break;

      // Update status to uploading
      updateFile(pendingItem.id, { status: "uploading", progress: 50 });

      try {
        // Upload the file
        const response = await uploadMutation.mutateAsync(pendingItem.file);

        // Update status to completed
        updateFile(pendingItem.id, {
          status: "completed",
          progress: 100,
          response,
        });
      } catch (error) {
        // Update status to failed
        updateFile(pendingItem.id, {
          status: "failed",
          progress: 0,
          error: error instanceof Error ? error.message : "Upload failed",
        });
      }

      // Get updated queue for next iteration
      currentQueue = await new Promise<QueuedFile[]>((resolve) => {
        setQueue((prev) => {
          resolve(prev);
          return prev;
        });
      });
    }

    isProcessingRef.current = false;
    setIsUploading(false);
  }, [queue, updateFile, uploadMutation]);

  /**
   * Start uploading pending files
   */
  const startUpload = useCallback(() => {
    if (!isUploading) {
      processQueue();
    }
  }, [isUploading, processQueue]);

  /**
   * Cancel ongoing upload
   */
  const cancelUpload = useCallback(() => {
    cancelledRef.current = true;
  }, []);

  /**
   * Clear completed and failed files
   */
  const clearCompleted = useCallback(() => {
    setQueue((prev) =>
      prev.filter(
        (item) => item.status !== "completed" && item.status !== "failed"
      )
    );
  }, []);

  /**
   * Clear entire queue
   */
  const clearAll = useCallback(() => {
    if (!isUploading) {
      setQueue([]);
    }
  }, [isUploading]);

  /**
   * Retry a failed upload
   */
  const retryFile = useCallback((id: string) => {
    setQueue((prev) =>
      prev.map((item) =>
        item.id === id && item.status === "failed"
          ? { ...item, status: "pending", error: undefined, progress: 0 }
          : item
      )
    );
  }, []);

  // Calculate counts
  const totalFiles = queue.length;
  const completedFiles = queue.filter((f) => f.status === "completed").length;
  const failedFiles = queue.filter((f) => f.status === "failed").length;
  const pendingFiles = queue.filter((f) => f.status === "pending").length;

  return {
    queue,
    addFiles,
    removeFile,
    startUpload,
    clearCompleted,
    clearAll,
    retryFile,
    cancelUpload,
    isUploading,
    totalFiles,
    completedFiles,
    failedFiles,
    pendingFiles,
  };
}
