/**
 * Zod schemas for runtime type validation.
 *
 * Ensures API responses match expected types at runtime,
 * catching issues before they reach components.
 */

import { z } from 'zod'

/**
 * Processing parameters schema.
 *
 * All canvas and line width parameters are required and must be positive.
 * Validation constraints match backend Pydantic models exactly.
 */
export const ProcessParamsSchema = z.object({
  // Required parameters with strict bounds matching backend
  canvas_width_mm: z.number().positive('Canvas width must be positive').max(5000),
  canvas_height_mm: z.number().positive('Canvas height must be positive').max(5000),
  line_width_mm: z.number().positive('Line width must be positive').max(10),

  // Optional boolean flags
  isolate_subject: z.boolean().optional(),
  use_ml: z.boolean().optional(),

  // Edge detection parameters
  edge_threshold: z.tuple([z.number().int(), z.number().int()]).optional().refine(
    (val) => !val || (val[0] >= 0 && val[0] < val[1] && val[1] <= 255),
    { message: 'Edge threshold must be 0 <= low < high <= 255' }
  ),
  line_threshold: z.number().int().min(1).max(255).optional(),

  // Optimization parameters
  merge_tolerance: z.number().min(0).max(10).optional(),
  simplify_tolerance: z.number().min(0).max(10).optional(),

  // Hatching parameters
  hatching_enabled: z.boolean().optional(),
  hatch_density: z.number().positive().max(10).optional(),
  hatch_angle: z.number().int().min(-180).max(180).optional(),
  darkness_threshold: z.number().int().min(0).max(255).optional(),
})

export type ProcessParams = z.infer<typeof ProcessParamsSchema>

/**
 * Upload response schema.
 */
export const UploadResponseSchema = z.object({
  job_id: z.string().uuid('Invalid job ID format'),
  filename: z.string().min(1, 'Filename required'),
  image_url: z.string().min(1), // Backend returns path string, not full URL
})

export type UploadResponse = z.infer<typeof UploadResponseSchema>

/**
 * Job statistics schema.
 */
export const JobStatsSchema = z.object({
  path_count: z.number().int().nonnegative(),
  total_length_mm: z.number().nonnegative(),
  width_mm: z.number().positive().nullable().optional(), // Backend can send null
  height_mm: z.number().positive().nullable().optional(), // Backend can send null
})

export type JobStats = z.infer<typeof JobStatsSchema>

/**
 * Processing status enum.
 */
export const ProcessingStatusSchema = z.enum(['pending', 'processing', 'completed', 'failed'])

export type ProcessingStatus = z.infer<typeof ProcessingStatusSchema>

/**
 * Job status response schema.
 */
export const JobStatusResponseSchema = z.object({
  job_id: z.string().uuid(),
  status: ProcessingStatusSchema,
  progress: z.number().int().min(0).max(100), // Backend returns int, not float
  result_url: z.string().optional(), // Backend may return non-URL strings
  stats: JobStatsSchema.optional(),
  error: z.string().optional(),
  device_used: z.string().optional(),
})

export type JobStatusResponse = z.infer<typeof JobStatusResponseSchema>

/**
 * Process request schema (for sending to API).
 */
export const ProcessRequestSchema = z.object({
  job_id: z.string().uuid(),
  mode: z.string(),
  params: ProcessParamsSchema.optional(),
})

export type ProcessRequest = z.infer<typeof ProcessRequestSchema>

/**
 * Process response schema.
 */
export const ProcessResponseSchema = z.object({
  job_id: z.string().uuid(),
  status: ProcessingStatusSchema,
  message: z.string(),
})

export type ProcessResponse = z.infer<typeof ProcessResponseSchema>

/**
 * Error response schema.
 */
export const ErrorResponseSchema = z.object({
  detail: z.string(),
})

export type ErrorResponse = z.infer<typeof ErrorResponseSchema>
