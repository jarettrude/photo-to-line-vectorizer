/**
 * Tests for Upload component.
 *
 * Validates file upload, drag-and-drop, validation, and error handling.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Upload } from './Upload'
import * as api from '@/lib/api'

// Mock API module
vi.mock('@/lib/api')

describe('Upload Component', () => {
  const mockOnUploadComplete = vi.fn()
  const mockUploadImage = vi.mocked(api.uploadImage)

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders upload area', () => {
    render(<Upload onUploadComplete={mockOnUploadComplete} />)

    expect(screen.getByText('Drop your image here')).toBeInTheDocument()
    expect(
      screen.getByText(/or click to browse \(JPEG, PNG, TIFF, WebP, HEIC\/HEIF\)/i)
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /choose file/i })).toBeInTheDocument()
  })

  it('handles file selection via input', async () => {
    const user = userEvent.setup()
    mockUploadImage.mockResolvedValue({
      job_id: 'test-job-123',
      filename: 'test.jpg',
      image_url: '/api/uploads/test-job-123.jpg',
    })

    render(<Upload onUploadComplete={mockOnUploadComplete} />)

    const file = new File(['fake image content'], 'test.jpg', { type: 'image/jpeg' })
    const input = screen.getByLabelText(/drop your image here/i, { selector: 'input' })

    await user.upload(input, file)

    await waitFor(() => {
      expect(mockUploadImage).toHaveBeenCalledWith(file)
      expect(mockOnUploadComplete).toHaveBeenCalledWith({
        job_id: 'test-job-123',
        filename: 'test.jpg',
        image_url: '/api/uploads/test-job-123.jpg',
      })
    })
  })

  it('shows uploading state during upload', async () => {
    const user = userEvent.setup()
    mockUploadImage.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 1000)))

    render(<Upload onUploadComplete={mockOnUploadComplete} />)

    const file = new File(['fake'], 'test.jpg', { type: 'image/jpeg' })
    const input = screen.getByLabelText(/drop your image here/i, { selector: 'input' })

    await user.upload(input, file)

    await waitFor(() => {
      expect(screen.getByText('Uploading...')).toBeInTheDocument()
    })
  })

  it('validates file type', async () => {
    const user = userEvent.setup()
    render(<Upload onUploadComplete={mockOnUploadComplete} />)

    const invalidFile = new File(['fake'], 'test.txt', { type: 'text/plain' })
    const input = screen.getByLabelText(/drop your image here/i, { selector: 'input' })

    await user.upload(input, invalidFile)

    await waitFor(() => {
      expect(
        screen.getByText(/Unsupported file format.*JPEG, PNG, TIFF, WebP, or HEIC\/HEIF/i)
      ).toBeInTheDocument()
    })

    expect(mockUploadImage).not.toHaveBeenCalled()
  })

  it('validates file size', async () => {
    const user = userEvent.setup()
    render(<Upload onUploadComplete={mockOnUploadComplete} />)

    // Create 51MB file (exceeds 50MB limit)
    const largeFile = new File([new ArrayBuffer(51 * 1024 * 1024)], 'large.jpg', {
      type: 'image/jpeg',
    })
    const input = screen.getByLabelText(/drop your image here/i, { selector: 'input' })

    await user.upload(input, largeFile)

    await waitFor(() => {
      expect(screen.getByText(/File too large.*Maximum size is 50MB/i)).toBeInTheDocument()
    })

    expect(mockUploadImage).not.toHaveBeenCalled()
  })

  it('handles upload error', async () => {
    const user = userEvent.setup()
    mockUploadImage.mockRejectedValue(new Error('Network error'))

    render(<Upload onUploadComplete={mockOnUploadComplete} />)

    const file = new File(['fake'], 'test.jpg', { type: 'image/jpeg' })
    const input = screen.getByLabelText(/drop your image here/i, { selector: 'input' })

    await user.upload(input, file)

    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument()
    })

    expect(mockOnUploadComplete).not.toHaveBeenCalled()
  })

  it('handles drag and drop', async () => {
    mockUploadImage.mockResolvedValue({
      job_id: 'test-job-123',
      filename: 'test.jpg',
      image_url: '/api/uploads/test-job-123.jpg',
    })

    render(<Upload onUploadComplete={mockOnUploadComplete} />)

    const file = new File(['fake'], 'test.jpg', { type: 'image/jpeg' })
    const dropZone = screen.getByText('Drop your image here').closest('div')

    fireEvent.dragOver(dropZone!)
    expect(dropZone).toHaveClass('border-primary')

    fireEvent.drop(dropZone!, {
      dataTransfer: {
        files: [file],
      },
    })

    await waitFor(() => {
      expect(mockUploadImage).toHaveBeenCalledWith(file)
    })
  })

  it('resets drag state on drag leave', () => {
    render(<Upload onUploadComplete={mockOnUploadComplete} />)

    const dropZone = screen.getByText('Drop your image here').closest('div')

    fireEvent.dragOver(dropZone!)
    expect(dropZone).toHaveClass('border-primary')

    fireEvent.dragLeave(dropZone!)
    expect(dropZone).not.toHaveClass('border-primary')
  })

  it('accepts HEIC files', async () => {
    const user = userEvent.setup()
    mockUploadImage.mockResolvedValue({
      job_id: 'test-job-123',
      filename: 'photo.heic',
      image_url: '/api/uploads/test-job-123.heic',
    })

    render(<Upload onUploadComplete={mockOnUploadComplete} />)

    const heicFile = new File(['fake'], 'photo.heic', { type: 'image/heic' })
    const input = screen.getByLabelText(/drop your image here/i, { selector: 'input' })

    await user.upload(input, heicFile)

    await waitFor(() => {
      expect(mockUploadImage).toHaveBeenCalledWith(heicFile)
    })
  })

  it('disables input during upload', async () => {
    mockUploadImage.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 1000)))

    render(<Upload onUploadComplete={mockOnUploadComplete} />)

    const input = screen.getByLabelText(/drop your image here/i, {
      selector: 'input',
    }) as HTMLInputElement

    const file = new File(['fake'], 'test.jpg', { type: 'image/jpeg' })
    await userEvent.upload(input, file)

    await waitFor(() => {
      expect(input).toBeDisabled()
    })
  })
})
