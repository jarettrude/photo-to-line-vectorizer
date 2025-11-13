/**
 * Tests for Controls component.
 *
 * Validates parameter configuration, advanced options, and process triggering.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Controls } from './Controls'

describe('Controls Component', () => {
  const mockOnProcess = vi.fn()

  it('renders basic controls', () => {
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    expect(screen.getByLabelText('Canvas Width (mm)')).toBeInTheDocument()
    expect(screen.getByLabelText('Canvas Height (mm)')).toBeInTheDocument()
    expect(screen.getByLabelText('Line Width (mm)')).toBeInTheDocument()
    expect(screen.getByLabelText('Isolate Subject')).toBeInTheDocument()
    expect(screen.getByLabelText('Use ML-assisted Vectorization')).toBeInTheDocument()
    expect(screen.getByLabelText('Enable Hatching')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /process image/i })).toBeInTheDocument()
  })

  it('has correct default values', () => {
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    const canvasWidth = screen.getByLabelText('Canvas Width (mm)') as HTMLInputElement
    const canvasHeight = screen.getByLabelText('Canvas Height (mm)') as HTMLInputElement
    const lineWidth = screen.getByLabelText('Line Width (mm)') as HTMLInputElement

    expect(canvasWidth.value).toBe('300')
    expect(canvasHeight.value).toBe('200')
    expect(lineWidth.value).toBe('0.3')
  })

  it('updates canvas width when user types', async () => {
    const user = userEvent.setup()
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    const input = screen.getByLabelText('Canvas Width (mm)') as HTMLInputElement

    await user.clear(input)
    await user.type(input, '400')

    expect(input.value).toBe('400')
  })

  it('updates canvas height when user types', async () => {
    const user = userEvent.setup()
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    const input = screen.getByLabelText('Canvas Height (mm)') as HTMLInputElement

    await user.clear(input)
    await user.type(input, '250')

    expect(input.value).toBe('250')
  })

  it('updates line width when user types', async () => {
    const user = userEvent.setup()
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    const input = screen.getByLabelText('Line Width (mm)') as HTMLInputElement

    await user.clear(input)
    await user.type(input, '0.5')

    expect(input.value).toBe('0.5')
  })

  it('toggles isolate subject switch', async () => {
    const user = userEvent.setup()
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    const isolateSwitch = screen.getByLabelText('Isolate Subject')

    await user.click(isolateSwitch)

    expect(isolateSwitch).toBeChecked()
  })

  it('toggles ML switch', async () => {
    const user = userEvent.setup()
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    const mlSwitch = screen.getByLabelText('Use ML-assisted Vectorization')

    await user.click(mlSwitch)

    expect(mlSwitch).toBeChecked()
  })

  it('toggles hatching switch', async () => {
    const user = userEvent.setup()
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    const hatchingSwitch = screen.getByLabelText('Enable Hatching')

    await user.click(hatchingSwitch)

    expect(hatchingSwitch).toBeChecked()
  })

  it('shows advanced options when toggled', async () => {
    const user = userEvent.setup()
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    const advancedButton = screen.getByRole('button', { name: /show advanced options/i })

    await user.click(advancedButton)

    expect(screen.getByLabelText('Edge Threshold Low')).toBeInTheDocument()
    expect(screen.getByLabelText('Edge Threshold High')).toBeInTheDocument()
    expect(screen.getByLabelText('Line Threshold')).toBeInTheDocument()
    expect(screen.getByLabelText('Merge Tolerance (mm)')).toBeInTheDocument()
    expect(screen.getByLabelText('Simplify Tolerance (mm)')).toBeInTheDocument()
  })

  it('hides advanced options when toggled off', async () => {
    const user = userEvent.setup()
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    // Show advanced
    const advancedButton = screen.getByRole('button', { name: /show advanced options/i })
    await user.click(advancedButton)

    expect(screen.getByLabelText('Edge Threshold Low')).toBeInTheDocument()

    // Hide advanced
    await user.click(screen.getByRole('button', { name: /hide advanced options/i }))

    expect(screen.queryByLabelText('Edge Threshold Low')).not.toBeInTheDocument()
  })

  it('shows hatching options when hatching enabled', async () => {
    const user = userEvent.setup()
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    // Enable hatching and show advanced
    await user.click(screen.getByLabelText('Enable Hatching'))
    await user.click(screen.getByRole('button', { name: /show advanced options/i }))

    expect(screen.getByLabelText('Hatch Density')).toBeInTheDocument()
    expect(screen.getByLabelText('Darkness Threshold')).toBeInTheDocument()
  })

  it('calls onProcess with correct parameters', async () => {
    const user = userEvent.setup()
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    const processButton = screen.getByRole('button', { name: /process image/i })

    await user.click(processButton)

    expect(mockOnProcess).toHaveBeenCalledWith({
      canvas_width_mm: 300,
      canvas_height_mm: 200,
      line_width_mm: 0.3,
      isolate_subject: false,
      use_ml: false,
      edge_threshold: [50, 150],
      line_threshold: 16,
      merge_tolerance: 0.5,
      simplify_tolerance: 0.2,
      hatching_enabled: false,
      hatch_density: 2.0,
      hatch_angle: 45,
      darkness_threshold: 100,
    })
  })

  it('includes modified parameters in onProcess call', async () => {
    const user = userEvent.setup()
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    // Modify some values
    const widthInput = screen.getByLabelText('Canvas Width (mm)')
    await user.clear(widthInput)
    await user.type(widthInput, '400')

    await user.click(screen.getByLabelText('Use ML-assisted Vectorization'))

    const processButton = screen.getByRole('button', { name: /process image/i })
    await user.click(processButton)

    expect(mockOnProcess).toHaveBeenCalledWith(
      expect.objectContaining({
        canvas_width_mm: 400,
        use_ml: true,
      })
    )
  })

  it('disables process button when disabled prop is true', () => {
    render(<Controls onProcess={mockOnProcess} disabled={true} />)

    const processButton = screen.getByRole('button', { name: /process image/i })

    expect(processButton).toBeDisabled()
  })

  it('enables process button when disabled prop is false', () => {
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    const processButton = screen.getByRole('button', { name: /process image/i })

    expect(processButton).not.toBeDisabled()
  })

  it('respects input min/max constraints', () => {
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    const canvasWidth = screen.getByLabelText('Canvas Width (mm)') as HTMLInputElement
    const canvasHeight = screen.getByLabelText('Canvas Height (mm)') as HTMLInputElement
    const lineWidth = screen.getByLabelText('Line Width (mm)') as HTMLInputElement

    expect(canvasWidth).toHaveAttribute('min', '10')
    expect(canvasWidth).toHaveAttribute('max', '2000')
    expect(canvasHeight).toHaveAttribute('min', '10')
    expect(canvasHeight).toHaveAttribute('max', '2000')
    expect(lineWidth).toHaveAttribute('min', '0.1')
    expect(lineWidth).toHaveAttribute('max', '5')
  })

  it('updates advanced parameters', async () => {
    const user = userEvent.setup()
    render(<Controls onProcess={mockOnProcess} disabled={false} />)

    // Show advanced options
    await user.click(screen.getByRole('button', { name: /show advanced options/i }))

    // Modify advanced parameters
    const edgeLow = screen.getByLabelText('Edge Threshold Low')
    await user.clear(edgeLow)
    await user.type(edgeLow, '30')

    const processButton = screen.getByRole('button', { name: /process image/i })
    await user.click(processButton)

    expect(mockOnProcess).toHaveBeenCalledWith(
      expect.objectContaining({
        edge_threshold: [30, 150],
      })
    )
  })
})
