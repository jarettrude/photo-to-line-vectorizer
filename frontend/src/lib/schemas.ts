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
 * Optional parameters have sensible defaults defined in the backend.
 */
export const ProcessParamsSchema = z.object({
  canvas_width_mm: z.number().positive('Canvas width must be positive'),
  canvas_height_mm: z.number().positive('Canvas height must be positive'),
  line_width_mm: z.number().positive('Line width must be positive'),
  isolate_subject: z.boolean().optional(),
  use_ml: z.boolean().optional(),
  edge_threshold: z.tuple([z.number(), z.number()]).optional(),
  line_threshold: z.number().optional(),
  merge_tolerance: z.number().optional(),
  simplify_tolerance: z.number().optional(),
  hatching_enabled: z.boolean().optional(),
  hatch_density: z.number().optional(),
  hatch_angle: z.number().optional(),
  darkness_threshold: z.number().optional(),
})

export type ProcessParams = z.infer<typeof ProcessParamsSchema>

/**
 * Upload response schema.
 */
export const UploadResponseSchema = z.object({
  job_id: z.string().uuid('Invalid job ID format'),
  filename: z.string().min(1, 'Filename required'),
  image_url: z.string().url('Invalid image URL'),
})

export type UploadResponse = z.infer<typeof UploadResponseSchema>

/**
 * Job statistics schema.
 */
export const JobStatsSchema = z.object({
  path_count: z.number().int().nonnegative(),
  total_length_mm: z.number().nonnegative(),
  width_mm: z.number().positive().optional(),
  height_mm: z.number().positive().optional(),
})

export type JobStats = z.infer<typeof JobStatsSchema>

/**
 * Processing status enum.
 */
export const ProcessingStatusSchema = z.enum([
  'pending',
  'processing',
  'completed',
  'failed',
])

export type ProcessingStatus = z.infer<typeof ProcessingStatusSchema>

/**
 * Job status response schema.
 */
export const JobStatusResponseSchema = z.object({
  job_id: z.string().uuid(),
  status: ProcessingStatusSchema,
  progress: z.number().min(0).max(100),
  result_url: z.string().url().optional(),
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
 * Error response schema.
 */
export const ErrorResponseSchema = z.object({
  detail: z.string(),
})

export type ErrorResponse = z.infer<typeof ErrorResponseSchema>
