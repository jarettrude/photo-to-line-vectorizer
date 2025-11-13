/**
 * Storybook stories for Controls component.
 *
 * Demonstrates processing parameter configuration and advanced options.
 */
import type { Meta, StoryObj } from '@storybook/react-vite'
import { Controls } from './Controls'

const meta = {
  title: 'Components/Controls',
  component: Controls,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    onProcess: { action: 'process triggered' },
    disabled: {
      control: 'boolean',
      description: 'Disables the process button',
    },
  },
  args: {
    onProcess: () => {},
    disabled: false,
  },
} satisfies Meta<typeof Controls>

export default meta
type Story = StoryObj<typeof meta>

/**
 * Default state with standard parameters.
 * Canvas: 300x200mm, Line Width: 0.3mm
 */
export const Default: Story = {
  args: {},
}

/**
 * Interactive demo showing all available controls.
 * Try adjusting canvas size, line width, and toggling ML features.
 */
export const Interactive: Story = {
  args: {},
  parameters: {
    docs: {
      description: {
        story: `
**Main Controls:**
- Canvas Width/Height: Output dimensions in millimeters
- Line Width: Stroke width for generated paths
- Isolate Subject: Use U2Net model for background removal
- ML-assisted Vectorization: Enhanced edge detection using ML
- Enable Hatching: Add cross-hatching for shading

**Advanced Options:**
Click "Show Advanced Options" to access fine-tuning parameters for edge detection, merging, and simplification.
        `,
      },
    },
  },
}

/**
 * Controls in disabled state during processing.
 */
export const Disabled: Story = {
  args: {
    disabled: true,
  },
  parameters: {
    docs: {
      description: {
        story: 'The process button is disabled while an image is being processed.',
      },
    },
  },
}

/**
 * Preset for small canvas output (business card size).
 * 90mm x 50mm canvas
 */
export const SmallCanvas: Story = {
  args: {},
  parameters: {
    docs: {
      description: {
        story: `
**Small Canvas Preset:**
Ideal for business cards, stickers, or small prints.
- Recommended: 90mm x 50mm
- Line Width: 0.2mm for fine detail
        `,
      },
    },
  },
}

/**
 * Preset for large canvas output (poster size).
 * 800mm x 600mm canvas
 */
export const LargeCanvas: Story = {
  args: {},
  parameters: {
    docs: {
      description: {
        story: `
**Large Canvas Preset:**
Ideal for posters, wall art, or large prints.
- Recommended: 800mm x 600mm
- Line Width: 0.5mm for visible lines at scale
        `,
      },
    },
  },
}

/**
 * Configuration with ML features enabled.
 * Shows the recommended setup for high-quality output.
 */
export const WithMLEnabled: Story = {
  args: {},
  parameters: {
    docs: {
      description: {
        story: `
**ML-Enhanced Configuration:**
- Isolate Subject: Removes background for cleaner output
- ML-assisted Vectorization: Improves edge detection quality
- Best for: Portrait photos, objects with complex backgrounds
        `,
      },
    },
  },
}

/**
 * Configuration with hatching enabled for shading effects.
 */
export const WithHatching: Story = {
  args: {},
  parameters: {
    docs: {
      description: {
        story: `
**Hatching Configuration:**
Adds cross-hatching lines to represent darker areas, creating depth and shading.
- Enable "Show Advanced Options" to see Hatch Density and Darkness Threshold controls
- Hatch Density: Controls spacing between hatch lines (higher = denser)
- Darkness Threshold: Defines which areas receive hatching (lower = more hatching)
        `,
      },
    },
  },
}

/**
 * Responsive layout in a constrained container.
 */
export const InContainer: Story = {
  args: {},
  decorators: [
    (Story) => (
      <div style={{ width: '400px', padding: '20px', border: '1px dashed #ccc' }}>
        <Story />
      </div>
    ),
  ],
  parameters: {
    docs: {
      description: {
        story: 'Controls component adapts to container width and maintains usability.',
      },
    },
  },
}

/**
 * Documentation of parameter ranges and effects.
 */
export const ParameterGuide: Story = {
  args: {},
  parameters: {
    docs: {
      description: {
        story: `
## Parameter Reference

### Canvas Dimensions
- **Range:** 10-2000mm
- **Default:** 300mm x 200mm (A4-ish landscape)
- **Effect:** Final output size. Larger canvases preserve more detail.

### Line Width
- **Range:** 0.1-5mm
- **Default:** 0.3mm
- **Effect:** Stroke width of paths. Thinner lines = more detail, but harder to plot.

### Edge Threshold (Advanced)
- **Range:** 0-255 each (Low, High)
- **Default:** [50, 150]
- **Effect:** Canny edge detection sensitivity. Lower = more edges detected.

### Line Threshold (Advanced)
- **Range:** 0-255
- **Default:** 16
- **Effect:** Hough line detection sensitivity. Lower = more lines detected.

### Merge Tolerance (Advanced)
- **Range:** 0-5mm
- **Default:** 0.5mm
- **Effect:** Distance threshold for merging nearby endpoints.

### Simplify Tolerance (Advanced)
- **Range:** 0-5mm
- **Default:** 0.2mm
- **Effect:** Path simplification aggressiveness. Higher = smoother but less detailed.

### Hatch Density (Advanced, when hatching enabled)
- **Range:** 0.5-5
- **Default:** 2.0
- **Effect:** Spacing between hatch lines. Higher = denser hatching.

### Darkness Threshold (Advanced, when hatching enabled)
- **Range:** 0-255
- **Default:** 100
- **Effect:** Which pixels get hatching. Lower threshold = more area hatched.
        `,
      },
    },
  },
}
