/**
 * Storybook stories for WelcomeScreen component.
 */
import type { Meta, StoryObj } from '@storybook/react-vite'
import { WelcomeScreen } from './WelcomeScreen'

const meta = {
  title: 'Components/WelcomeScreen',
  component: WelcomeScreen,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof WelcomeScreen>

export default meta
type Story = StoryObj<typeof meta>

/**
 * Default welcome screen shown when no image is uploaded.
 * Provides an overview of features and supported formats.
 */
export const Default: Story = {}

/**
 * Welcome screen in a container to show responsive behavior.
 */
export const InContainer: Story = {
  decorators: [
    (Story) => (
      <div className="max-w-4xl mx-auto">
        <Story />
      </div>
    ),
  ],
}
