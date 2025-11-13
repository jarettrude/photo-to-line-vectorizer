/**
 * API client for photo-to-line-vectorizer backend.
 *
 * Provides typed interfaces for all API endpoints.
 */

export interface ProcessParams {
  canvas_width_mm: number
  canvas_height_mm: number
  line_width_mm: number
  isolate_subject?: boolean
  use_ml?: boolean
  edge_threshold?: [number, number]
  line_threshold?: number
  merge_tolerance?: number
  simplify_tolerance?: number
  hatching_enabled?: boolean
  hatch_density?: number
  hatch_angle?: number
  darkness_threshold?: number
}

export interface UploadResponse {
  job_id: string
  filename: string
  image_url: string
}

export interface JobStats {
  path_count: number
  total_length_mm: number
  width_mm?: number
  height_mm?: number
}

export interface JobStatusResponse {
  job_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  result_url?: string
  stats?: JobStats
  error?: string
  device_used?: string
}

const API_BASE = '/api'

export async function uploadImage(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${API_BASE}/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Upload failed')
  }

  return response.json()
}

export async function processImage(
  jobId: string,
  mode: string = 'auto',
  params?: ProcessParams
): Promise<void> {
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
    const error = await response.json()
    throw new Error(error.detail || 'Processing failed')
  }
}

export async function getJobStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE}/status/${jobId}`)

  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to get status')
  }

  return response.json()
}

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/download/${jobId}`
}
