/**
 * API client for photo-to-line-vectorizer backend.
 *
 * Provides typed interfaces with runtime validation using Zod.
 * All API responses are validated to ensure type safety.
 */

import {
  ProcessParams,
  UploadResponse,
  UploadResponseSchema,
  JobStatusResponse,
  JobStatusResponseSchema,
  ProcessResponse,
  ProcessResponseSchema,
  ErrorResponseSchema,
} from './schemas'

// Re-export types for external use
export type { ProcessParams, UploadResponse, JobStatusResponse, ProcessResponse }

const API_BASE = '/api'

/**
 * Custom error class for API errors.
 */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * Parse error response from API.
 */
async function parseError(response: Response): Promise<never> {
  try {
    const error = await response.json()
    const validated = ErrorResponseSchema.parse(error)
    throw new ApiError(validated.detail || 'Request failed', response.status, validated.detail)
  } catch (e) {
    if (e instanceof ApiError) throw e
    throw new ApiError(`Request failed with status ${response.status}`, response.status)
  }
}

/**
 * Upload image file for processing.
 *
 * @param file - Image file (JPEG, PNG, TIFF, WebP, HEIC/HEIF)
 * @returns Upload response with job_id
 * @throws ApiError if upload fails or file invalid
 */
export async function uploadImage(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    await parseError(response)
  }

  const data = await response.json()

  // Runtime validation with Zod
  try {
    return UploadResponseSchema.parse(data)
  } catch (e) {
    console.error('Invalid upload response:', e)
    throw new ApiError('Invalid response from server', 500)
  }
}

/**
 * Start processing an uploaded image.
 *
 * @param jobId - Job identifier from upload
 * @param mode - Processing mode (usually 'auto')
 * @param params - Optional processing parameters
 * @returns Process response with job status
 * @throws ApiError if processing fails to start
 */
export async function processImage(
  jobId: string,
  mode: string = 'auto',
  params?: ProcessParams
): Promise<ProcessResponse> {
  const response = await fetch(`${API_BASE}/process`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      job_id: jobId,
      mode,
      params,
    }),
  })

  if (!response.ok) {
    await parseError(response)
  }

  const data = await response.json()

  // Runtime validation with Zod
  try {
    return ProcessResponseSchema.parse(data)
  } catch (e) {
    console.error('Invalid process response:', e)
    throw new ApiError('Invalid response from server', 500)
  }
}

/**
 * Get job status with progress and results.
 *
 * @param jobId - Job identifier
 * @returns Job status with progress, results, and stats
 * @throws ApiError if job not found
 */
export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE}/status/${jobId}`)

  if (!response.ok) {
    await parseError(response)
  }

  const data = await response.json()

  // Runtime validation with Zod
  try {
    return JobStatusResponseSchema.parse(data)
  } catch (e) {
    console.error('Invalid status response:', e)
    throw new ApiError('Invalid response from server', 500)
  }
}

/**
 * Get download URL for result file.
 *
 * @param jobId - Job identifier
 * @param format - Export format (svg, hpgl, gcode)
 * @returns Download URL
 */
export function getDownloadUrl(jobId: string, format: string = 'svg'): string {
  return `${API_BASE}/download/${jobId}?export_format=${format}`
}

/**
 * Download result file.
 *
 * @param jobId - Job identifier
 * @param format - Export format (svg, hpgl, gcode)
 * @throws ApiError if download fails
 */
export async function downloadResult(jobId: string, format: string = 'svg'): Promise<Blob> {
  const response = await fetch(getDownloadUrl(jobId, format))

  if (!response.ok) {
    await parseError(response)
  }

  return response.blob()
}
