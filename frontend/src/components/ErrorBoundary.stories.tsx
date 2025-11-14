/**
 * Storybook stories for ErrorBoundary component.
 */
import type { Meta, StoryObj } from '@storybook/react-vite'
import { ErrorBoundary } from './ErrorBoundary'
import { Button } from './ui/button'

const meta = {
  title: 'Components/ErrorBoundary',
  component: ErrorBoundary,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof ErrorBoundary>

export default meta
type Story = StoryObj<typeof meta>

const ThrowError = () => {
  throw new Error('This is a test error from Storybook')
}

/**
 * Example of error boundary catching an error.
 * Click the button to trigger an error.
 */
export const CaughtError: Story = {
  args: {
    children: <ThrowError />,
  },
}

/**
 * Error boundary with working children.
 */
export const WithValidChildren: Story = {
  args: {
    children: (
      <div className="p-8">
        <h1 className="text-2xl font-bold">Everything is working!</h1>
        <p className="text-muted-foreground mt-2">This content is rendered normally.</p>
      </div>
    ),
  },
}

/**
 * Custom fallback UI for error boundary.
 */
export const CustomFallback: Story = {
  args: {
    children: <ThrowError />,
    fallback: (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="text-center">
          <h1 className="text-2xl font-bold">Custom Error UI</h1>
          <p className="text-muted-foreground mt-2">This is a custom fallback component.</p>
          <Button className="mt-4" onClick={() => window.location.reload()}>
            Reload
          </Button>
        </div>
      </div>
    ),
  },
}
