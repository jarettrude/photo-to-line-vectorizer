/**
 * Storybook stories for Button component.
 *
 * Demonstrates all button variants, sizes, and states from the design system.
 */
import type { Meta, StoryObj } from '@storybook/react-vite'
import { Button } from './button'
import { Download, Upload, Play, Settings } from 'lucide-react'

const meta = {
  title: 'UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'],
      description: 'Visual style variant',
    },
    size: {
      control: 'select',
      options: ['default', 'sm', 'lg', 'icon'],
      description: 'Button size',
    },
    disabled: {
      control: 'boolean',
      description: 'Disabled state',
    },
    asChild: {
      control: 'boolean',
      description: 'Render as child component (Radix Slot)',
    },
    onClick: {
      action: 'clicked',
    },
  },
} satisfies Meta<typeof Button>

export default meta
type Story = StoryObj<typeof meta>

/**
 * Default primary button style.
 */
export const Default: Story = {
  args: {
    children: 'Button',
  },
}

/**
 * Destructive action button (delete, cancel, etc.).
 */
export const Destructive: Story = {
  args: {
    variant: 'destructive',
    children: 'Delete',
  },
}

/**
 * Outline button for secondary actions.
 */
export const Outline: Story = {
  args: {
    variant: 'outline',
    children: 'Cancel',
  },
}

/**
 * Secondary button for less prominent actions.
 */
export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Secondary',
  },
}

/**
 * Ghost button with minimal styling.
 */
export const Ghost: Story = {
  args: {
    variant: 'ghost',
    children: 'Ghost',
  },
}

/**
 * Link-styled button.
 */
export const Link: Story = {
  args: {
    variant: 'link',
    children: 'Link Button',
  },
}

/**
 * Small size button.
 */
export const Small: Story = {
  args: {
    size: 'sm',
    children: 'Small Button',
  },
}

/**
 * Large size button.
 */
export const Large: Story = {
  args: {
    size: 'lg',
    children: 'Large Button',
  },
}

/**
 * Icon-only button (square).
 */
export const Icon: Story = {
  args: {
    size: 'icon',
    children: <Settings className="w-4 h-4" />,
  },
}

/**
 * Disabled button state.
 */
export const Disabled: Story = {
  args: {
    disabled: true,
    children: 'Disabled',
  },
}

/**
 * Button with leading icon.
 */
export const WithLeadingIcon: Story = {
  args: {
    children: (
      <>
        <Upload className="w-4 h-4 mr-2" />
        Upload Image
      </>
    ),
  },
}

/**
 * Button with trailing icon.
 */
export const WithTrailingIcon: Story = {
  args: {
    children: (
      <>
        Download
        <Download className="w-4 h-4 ml-2" />
      </>
    ),
  },
}

/**
 * Large button with icon (like Process button).
 */
export const LargeWithIcon: Story = {
  args: {
    size: 'lg',
    children: (
      <>
        <Play className="w-4 h-4 mr-2" />
        Process Image
      </>
    ),
  },
}

/**
 * Full width button.
 */
export const FullWidth: Story = {
  args: {
    className: 'w-full',
    size: 'lg',
    children: 'Full Width Button',
  },
  decorators: [
    (Story) => (
      <div style={{ width: '400px' }}>
        <Story />
      </div>
    ),
  ],
}

/**
 * Button as anchor link (using asChild).
 */
export const AsLink: Story = {
  args: {
    asChild: true,
    children: (
      <a href="#download" download>
        <Download className="w-4 h-4 mr-2" />
        Download Result
      </a>
    ),
  },
  parameters: {
    docs: {
      description: {
        story: 'Uses Radix Slot to render as an anchor tag while maintaining button styling.',
      },
    },
  },
}

/**
 * All variants comparison.
 */
export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      <Button variant="default">Default</Button>
      <Button variant="destructive">Destructive</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="link">Link</Button>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Comparison of all available button variants.',
      },
    },
  },
}

/**
 * All sizes comparison.
 */
export const AllSizes: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      <Button size="sm">Small</Button>
      <Button size="default">Default</Button>
      <Button size="lg">Large</Button>
      <Button size="icon">
        <Settings className="w-4 h-4" />
      </Button>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Comparison of all available button sizes.',
      },
    },
  },
}

/**
 * Button group layout.
 */
export const ButtonGroup: Story = {
  render: () => (
    <div className="flex gap-2">
      <Button variant="outline">Cancel</Button>
      <Button>Confirm</Button>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Common pattern: Cancel (outline) and Confirm (primary) buttons side by side.',
      },
    },
  },
}

/**
 * Loading state button.
 */
export const Loading: Story = {
  args: {
    disabled: true,
    children: (
      <>
        <div className="w-4 h-4 mr-2 border-2 border-current border-t-transparent rounded-full animate-spin" />
        Processing...
      </>
    ),
  },
  parameters: {
    docs: {
      description: {
        story: 'Common pattern for showing loading state during async operations.',
      },
    },
  },
}

/**
 * Design system reference.
 */
export const DesignSystem: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Button Variants</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-muted-foreground mb-2">Primary Actions</p>
            <Button className="w-full">Default</Button>
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-2">Destructive Actions</p>
            <Button variant="destructive" className="w-full">
              Destructive
            </Button>
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-2">Secondary Actions</p>
            <Button variant="outline" className="w-full">
              Outline
            </Button>
          </div>
          <div>
            <p className="text-sm text-muted-foreground mb-2">Tertiary Actions</p>
            <Button variant="ghost" className="w-full">
              Ghost
            </Button>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Button Sizes</h3>
        <div className="flex items-center gap-4">
          <Button size="sm">Small</Button>
          <Button size="default">Default</Button>
          <Button size="lg">Large</Button>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">With Icons</h3>
        <div className="flex flex-wrap gap-4">
          <Button>
            <Upload className="w-4 h-4 mr-2" />
            Upload
          </Button>
          <Button variant="outline">
            <Download className="w-4 h-4 mr-2" />
            Download
          </Button>
          <Button size="icon" variant="ghost">
            <Settings className="w-4 h-4" />
          </Button>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">States</h3>
        <div className="flex gap-4">
          <Button>Normal</Button>
          <Button disabled>Disabled</Button>
        </div>
      </div>
    </div>
  ),
  parameters: {
    layout: 'padded',
    docs: {
      description: {
        story:
          'Complete design system reference showing all button styles, sizes, and usage patterns.',
      },
    },
  },
}
