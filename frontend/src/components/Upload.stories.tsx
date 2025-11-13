/**
 * Storybook stories for Upload component.
 *
 * Demonstrates all states and interactions for the image upload component.
 */
import type { Meta, StoryObj } from '@storybook/react-vite'
import { Upload } from './Upload'

const meta = {
  title: 'Components/Upload',
  component: Upload,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    onUploadComplete: { action: 'upload complete' },
  },
  args: {
    onUploadComplete: () => {},
  },
} satisfies Meta<typeof Upload>

export default meta
type Story = StoryObj<typeof meta>

/**
 * Default state of the upload component.
 * Ready to accept file uploads via drag-and-drop or file selection.
 */
export const Default: Story = {
  args: {},
}

/**
 * Component with focus on the dropzone area.
 * Demonstrates the interactive upload interface.
 */
export const Interactive: Story = {
  args: {},
  parameters: {
    docs: {
      description: {
        story:
          'Try dragging an image file onto the component or clicking to select a file. Supported formats: JPEG, PNG, TIFF, WebP, HEIC/HEIF.',
      },
    },
  },
}

/**
 * Documentation story showing supported file formats.
 */
export const SupportedFormats: Story = {
  args: {},
  parameters: {
    docs: {
      description: {
        story: `
**Supported Image Formats:**
- JPEG (.jpg, .jpeg)
- PNG (.png)
- TIFF (.tiff, .tif)
- WebP (.webp)
- HEIC/HEIF (.heic, .heif) - iPhone native format

**File Size Limit:** 50MB maximum
        `,
      },
    },
  },
}

/**
 * Example with custom styling context.
 * Shows how the component adapts to different container widths.
 */
export const InContainer: Story = {
  args: {},
  decorators: [
    (Story) => (
      <div style={{ width: '600px', padding: '20px', border: '1px dashed #ccc' }}>
        <Story />
      </div>
    ),
  ],
}

/**
 * Compact version for smaller layouts.
 */
export const Compact: Story = {
  args: {},
  decorators: [
    (Story) => (
      <div style={{ width: '400px' }}>
        <Story />
      </div>
    ),
  ],
}
