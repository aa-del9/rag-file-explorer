/**
 * Upload API client for IntelliFile
 * Handles document file uploads to the backend
 */

import { API_URL } from "@/lib/constants";

/**
 * Upload response from the backend
 */
export interface UploadResponse {
  success: boolean;
  message: string;
  document_id: string;
  filename: string;
  file_size_mb: number;
  chunk_count: number;
  processing_time_seconds: number;
  metadata: {
    title: string | null;
    author: string | null;
    page_count: number | null;
    ai_summary: string | null;
    ai_keywords: string[] | null;
    ai_document_type: string | null;
  };
}

/**
 * Upload error response
 */
export interface UploadError {
  detail: string;
}

/**
 * Upload a single document file to the backend
 * @param file - The file to upload
 * @returns Promise with upload response
 */
export async function uploadDocument2(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_URL}/upload/document`, {
    method: "POST",
    body: formData,
    // Don't set Content-Type header - let browser set it with boundary for multipart/form-data
  });

  if (!response.ok) {
    const errorData: UploadError = await response.json().catch(() => ({
      detail: `Upload failed: ${response.status} ${response.statusText}`,
    }));
    throw new Error(errorData.detail);
  }

  return response.json();
}

/**
 * Allowed file extensions for upload
 */
export const ALLOWED_EXTENSIONS = [".pdf", ".doc", ".docx"];

/**
 * Maximum file size in bytes (50MB)
 */
export const MAX_FILE_SIZE = 52428800;

/**
 * Validate a file before upload
 * @param file - The file to validate
 * @returns Object with isValid flag and optional error message
 */
export function validateFile(file: File): { isValid: boolean; error?: string } {
  // Check file extension
  const extension = `.${file.name.split(".").pop()?.toLowerCase()}`;
  if (!ALLOWED_EXTENSIONS.includes(extension)) {
    return {
      isValid: false,
      error: `File type ${extension} not supported. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`,
    };
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    return {
      isValid: false,
      error: `File too large. Maximum size: ${MAX_FILE_SIZE / 1024 / 1024}MB`,
    };
  }

  return { isValid: true };
}

/**
 * Format file size for display
 * @param bytes - File size in bytes
 * @returns Formatted string (e.g., "2.5 MB")
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Get file extension from filename
 * @param filename - The filename
 * @returns Extension including dot (e.g., ".pdf")
 */
export function getFileExtension(filename: string): string {
  return `.${filename.split(".").pop()?.toLowerCase() || ""}`;
}
