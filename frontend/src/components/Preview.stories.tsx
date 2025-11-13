/**
 * Storybook stories for Preview component.
 *
 * Demonstrates different job states, statistics display, and result preview.
 */
import type { Meta, StoryObj } from '@storybook/react-vite'
import { Preview } from './Preview'
import type { JobStatusResponse } from '@/lib/api'

const meta = {
  title: 'Components/Preview',
  component: Preview,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    jobStatus: {
      description: 'Current job status object or null',
    },
  },
} satisfies Meta<typeof Preview>

export default meta
type Story = StoryObj<typeof meta>

/**
 * Empty state when no image has been uploaded.
 */
export const Empty: Story = {
  args: {
    jobStatus: null,
  },
  parameters: {
    docs: {
      description: {
        story: 'Initial state before any image is uploaded or processed.',
      },
    },
  },
}

/**
 * Processing state at 25% progress.
 */
export const ProcessingEarly: Story = {
  args: {
    jobStatus: {
      job_id: 'demo-job-1',
      status: 'processing',
      progress: 25,
      result_url: null,
      stats: null,
      error: null,
      device_used: 'cuda',
    } as JobStatusResponse,
  },
  parameters: {
    docs: {
      description: {
        story: 'Shows animated spinner and progress percentage. Displays the computing device being used (cuda/cpu).',
      },
    },
  },
}

/**
 * Processing state at 75% progress.
 */
export const ProcessingLate: Story = {
  args: {
    jobStatus: {
      job_id: 'demo-job-2',
      status: 'processing',
      progress: 75,
      result_url: null,
      stats: null,
      error: null,
      device_used: 'cpu',
    } as JobStatusResponse,
  },
  parameters: {
    docs: {
      description: {
        story: 'Near completion of processing. Device used is CPU in this example.',
      },
    },
  },
}

/**
 * Processing state without device information.
 */
export const ProcessingNoDevice: Story = {
  args: {
    jobStatus: {
      job_id: 'demo-job-3',
      status: 'processing',
      progress: 50,
      result_url: null,
      stats: null,
      error: null,
      device_used: null,
    } as JobStatusResponse,
  },
  parameters: {
    docs: {
      description: {
        story: 'Processing state when device information is not available.',
      },
    },
  },
}

/**
 * Completed job with full statistics.
 */
export const CompletedWithStats: Story = {
  args: {
    jobStatus: {
      job_id: 'demo-completed-1',
      status: 'completed',
      progress: 100,
      result_url: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyMDAiIGhlaWdodD0iMTUwIj48cGF0aCBkPSJNMTAgMTBMMTkwIDE0ME0xMCAxNDBMMTkwIDEwIiBzdHJva2U9ImJsYWNrIiBmaWxsPSJub25lIiBzdHJva2Utd2lkdGg9IjIiLz48L3N2Zz4=',
      stats: {
        path_count: 42,
        total_length_mm: 1234.56,
        width_mm: 200.0,
        height_mm: 150.0,
      },
      error: null,
      device_used: 'cuda',
    } as JobStatusResponse,
  },
  parameters: {
    docs: {
      description: {
        story: `
**Completed State Features:**
- SVG preview in iframe
- Path count and total length statistics
- Canvas dimensions (width x height)
- Processing device information
- Download button with direct link

This story uses a base64-encoded SVG for demonstration.
        `,
      },
    },
  },
}

/**
 * Completed job with complex path statistics.
 */
export const CompletedComplex: Story = {
  args: {
    jobStatus: {
      job_id: 'demo-completed-2',
      status: 'completed',
      progress: 100,
      result_url: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0MDAiIGhlaWdodD0iMzAwIj48cGF0aCBkPSJNNTAgNTBRMTAwIDUwIDE1MCAxMDBUMjUwIDE1MCIgc3Ryb2tlPSJibGFjayIgZmlsbD0ibm9uZSIgc3Ryb2tlLXdpZHRoPSIxLjUiLz48cGF0aCBkPSJNMzAwIDUwTDM1MCAyNTBNNTAgMjUwTDM1MCAyNTAiIHN0cm9rZT0iYmxhY2siIGZpbGw9Im5vbmUiIHN0cm9rZS13aWR0aD0iMS41Ii8+PC9zdmc+',
      stats: {
        path_count: 156,
        total_length_mm: 4567.89,
        width_mm: 400.0,
        height_mm: 300.0,
      },
      error: null,
      device_used: 'cpu',
    } as JobStatusResponse,
  },
  parameters: {
    docs: {
      description: {
        story: 'A more complex result with many paths and longer total length. Useful for testing stat display formatting.',
      },
    },
  },
}

/**
 * Completed job without dimension statistics.
 */
export const CompletedNoDimensions: Story = {
  args: {
    jobStatus: {
      job_id: 'demo-completed-3',
      status: 'completed',
      progress: 100,
      result_url: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodD0iMTAwIj48Y2lyY2xlIGN4PSI1MCIgY3k9IjUwIiByPSI0MCIgc3Ryb2tlPSJibGFjayIgZmlsbD0ibm9uZSIgc3Ryb2tlLXdpZHRoPSIyIi8+PC9zdmc+',
      stats: {
        path_count: 12,
        total_length_mm: 345.67,
        width_mm: null,
        height_mm: null,
      },
      error: null,
      device_used: null,
    } as JobStatusResponse,
  },
  parameters: {
    docs: {
      description: {
        story: 'When width and height are not available, they are not displayed in the stats grid.',
      },
    },
  },
}

/**
 * Completed job without any statistics.
 */
export const CompletedNoStats: Story = {
  args: {
    jobStatus: {
      job_id: 'demo-completed-4',
      status: 'completed',
      progress: 100,
      result_url: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI1MCIgaGVpZ2h0PSI1MCI+PHJlY3QgeD0iMTAiIHk9IjEwIiB3aWR0aD0iMzAiIGhlaWdodD0iMzAiIHN0cm9rZT0iYmxhY2siIGZpbGw9Im5vbmUiIHN0cm9rZS13aWR0aD0iMiIvPjwvc3ZnPg==',
      stats: null,
      error: null,
      device_used: null,
    } as JobStatusResponse,
  },
  parameters: {
    docs: {
      description: {
        story: 'Minimal completed state with only the SVG preview and download button, no statistics.',
      },
    },
  },
}

/**
 * Failed job with error message.
 */
export const FailedWithError: Story = {
  args: {
    jobStatus: {
      job_id: 'demo-failed-1',
      status: 'failed',
      progress: 0,
      result_url: null,
      stats: null,
      error: 'Out of memory: Image resolution too high for available GPU memory.',
      device_used: null,
    } as JobStatusResponse,
  },
  parameters: {
    docs: {
      description: {
        story: 'Error state with specific error message displayed to help user diagnose the issue.',
      },
    },
  },
}

/**
 * Failed job with generic error.
 */
export const FailedGeneric: Story = {
  args: {
    jobStatus: {
      job_id: 'demo-failed-2',
      status: 'failed',
      progress: 0,
      result_url: null,
      stats: null,
      error: null,
      device_used: null,
    } as JobStatusResponse,
  },
  parameters: {
    docs: {
      description: {
        story: 'Generic failure state when no specific error message is available.',
      },
    },
  },
}

/**
 * Responsive layout in a wide container.
 */
export const InWideContainer: Story = {
  args: {
    jobStatus: {
      job_id: 'demo-wide',
      status: 'completed',
      progress: 100,
      result_url: 'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIj48cGF0aCBkPSJNNTAgNTBMMjUwIDE1ME01MCAxNTBMMjUwIDUwIiBzdHJva2U9ImJsYWNrIiBmaWxsPSJub25lIiBzdHJva2Utd2lkdGg9IjIiLz48L3N2Zz4=',
      stats: {
        path_count: 28,
        total_length_mm: 892.34,
        width_mm: 300.0,
        height_mm: 200.0,
      },
      error: null,
      device_used: 'cuda',
    } as JobStatusResponse,
  },
  decorators: [
    (Story) => (
      <div style={{ width: '800px', padding: '20px', border: '1px dashed #ccc' }}>
        <Story />
      </div>
    ),
  ],
  parameters: {
    docs: {
      description: {
        story: 'Preview component in a wide container, showing how it adapts to available space.',
      },
    },
  },
}

/**
 * State transition demonstration.
 */
export const StateTransitions: Story = {
  args: {
    jobStatus: {
      job_id: 'demo-transition',
      status: 'processing',
      progress: 60,
      result_url: null,
      stats: null,
      error: null,
      device_used: 'cuda',
    } as JobStatusResponse,
  },
  parameters: {
    docs: {
      description: {
        story: `
## Job State Flow

1. **null:** Empty state, awaiting upload
2. **processing (0-100%):** Active processing with animated spinner
3. **completed:** Shows SVG preview, statistics, and download button
4. **failed:** Displays error message in destructive styling

The component automatically updates its display based on the jobStatus prop.
        `,
      },
    },
  },
}
