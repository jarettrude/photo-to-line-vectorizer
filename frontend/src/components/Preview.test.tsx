/**
 * Tests for Preview component.
 *
 * Validates different job states, stats display, and download functionality.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Preview } from './Preview'
import type { JobStatusResponse } from '@/lib/api'
import * as api from '@/lib/api'

// Mock API module
vi.mock('@/lib/api', async () => {
  const actual = await vi.importActual<typeof api>('@/lib/api')
  return {
    ...actual,
    getDownloadUrl: vi.fn((jobId: string) => `/api/download/${jobId}?format=svg`),
  }
})

describe('Preview Component', () => {
  it('renders empty state when no job status', () => {
    render(<Preview jobStatus={null} />)

    expect(screen.getByText('Preview')).toBeInTheDocument()
    expect(screen.getByText('Upload and process an image to see the result')).toBeInTheDocument()
  })

  it('renders processing state', () => {
    const jobStatus: JobStatusResponse = {
      job_id: 'test-123',
      status: 'processing',
      progress: 45,
      result_url: undefined,
      stats: undefined,
      error: undefined,
      device_used: 'cuda',
    }

    render(<Preview jobStatus={jobStatus} />)

    expect(screen.getByText('Processing... 45%')).toBeInTheDocument()
    expect(screen.getByText('Using: cuda')).toBeInTheDocument()
  })

  it('renders processing state without device', () => {
    const jobStatus: JobStatusResponse = {
      job_id: 'test-123',
      status: 'processing',
      progress: 30,
      result_url: undefined,
      stats: undefined,
      error: undefined,
      device_used: undefined,
    }

    render(<Preview jobStatus={jobStatus} />)

    expect(screen.getByText('Processing... 30%')).toBeInTheDocument()
    expect(screen.queryByText(/Using:/)).not.toBeInTheDocument()
  })

  it('renders failed state with error', () => {
    const jobStatus: JobStatusResponse = {
      job_id: 'test-123',
      status: 'failed',
      progress: 0,
      result_url: undefined,
      stats: undefined,
      error: 'Out of memory',
      device_used: undefined,
    }

    render(<Preview jobStatus={jobStatus} />)

    expect(screen.getByText('Processing failed')).toBeInTheDocument()
    expect(screen.getByText('Out of memory')).toBeInTheDocument()
  })

  it('renders failed state without specific error', () => {
    const jobStatus: JobStatusResponse = {
      job_id: 'test-123',
      status: 'failed',
      progress: 0,
      result_url: undefined,
      stats: undefined,
      error: undefined,
      device_used: undefined,
    }

    render(<Preview jobStatus={jobStatus} />)

    expect(screen.getByText('Processing failed')).toBeInTheDocument()
  })

  it('renders completed state with result', () => {
    const jobStatus: JobStatusResponse = {
      job_id: 'test-123',
      status: 'completed',
      progress: 100,
      result_url: '/api/uploads/test-123.svg',
      stats: {
        path_count: 42,
        total_length_mm: 1234.56,
        width_mm: 200.0,
        height_mm: 150.0,
      },
      error: undefined,
      device_used: 'cpu',
    }

    render(<Preview jobStatus={jobStatus} />)

    expect(screen.getByTitle('SVG Preview')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
    expect(screen.getByText('1234.56 mm')).toBeInTheDocument()
    expect(screen.getByText('200.00 mm')).toBeInTheDocument()
    expect(screen.getByText('150.00 mm')).toBeInTheDocument()
    expect(screen.getByText('Processed using: cpu')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /download svg/i })).toBeInTheDocument()
  })

  it('renders completed state without dimensions', () => {
    const jobStatus: JobStatusResponse = {
      job_id: 'test-456',
      status: 'completed',
      progress: 100,
      result_url: '/api/uploads/test-456.svg',
      stats: {
        path_count: 10,
        total_length_mm: 500.0,
        width_mm: undefined,
        height_mm: undefined,
      },
      error: undefined,
      device_used: undefined,
    }

    render(<Preview jobStatus={jobStatus} />)

    expect(screen.getByText('10')).toBeInTheDocument()
    expect(screen.getByText('500.00 mm')).toBeInTheDocument()
    // Width and height should not be rendered
    expect(screen.queryByText(/Width/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Height/)).not.toBeInTheDocument()
  })

  it('renders completed state without stats', () => {
    const jobStatus: JobStatusResponse = {
      job_id: 'test-789',
      status: 'completed',
      progress: 100,
      result_url: '/api/uploads/test-789.svg',
      stats: undefined,
      error: undefined,
      device_used: undefined,
    }

    render(<Preview jobStatus={jobStatus} />)

    expect(screen.getByTitle('SVG Preview')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: /download svg/i })).toBeInTheDocument()
    expect(screen.queryByText(/Path Count/)).not.toBeInTheDocument()
  })

  it('renders download link with correct URL', () => {
    const jobStatus: JobStatusResponse = {
      job_id: 'test-download-123',
      status: 'completed',
      progress: 100,
      result_url: '/api/uploads/test-download-123.svg',
      stats: undefined,
      error: undefined,
      device_used: undefined,
    }

    render(<Preview jobStatus={jobStatus} />)

    const downloadLink = screen.getByRole('link', { name: /download svg/i }) as HTMLAnchorElement
    expect(downloadLink.href).toContain('/api/download/test-download-123?format=svg')
  })

  it('displays spinner during processing', () => {
    const jobStatus: JobStatusResponse = {
      job_id: 'test-123',
      status: 'processing',
      progress: 50,
      result_url: undefined,
      stats: undefined,
      error: undefined,
      device_used: undefined,
    }

    render(<Preview jobStatus={jobStatus} />)

    const spinner = screen.getByRole('img', { hidden: true })
    expect(spinner.parentElement).toHaveClass('animate-spin')
  })

  it('displays iframe with correct src for completed job', () => {
    const jobStatus: JobStatusResponse = {
      job_id: 'test-123',
      status: 'completed',
      progress: 100,
      result_url: '/api/uploads/test-123.svg',
      stats: undefined,
      error: undefined,
      device_used: undefined,
    }

    render(<Preview jobStatus={jobStatus} />)

    const iframe = screen.getByTitle('SVG Preview') as HTMLIFrameElement
    expect(iframe.src).toContain('/api/uploads/test-123.svg')
  })
})
