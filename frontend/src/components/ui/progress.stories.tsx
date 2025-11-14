/**
 * Storybook stories for Progress component.
 */
import type { Meta, StoryObj } from '@storybook/react-vite'
import { Progress } from './progress'
import { useEffect, useState } from 'react'

const meta = {
  title: 'UI/Progress',
  component: Progress,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Progress>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    value: 50,
  },
  render: (args) => (
    <div className="w-80">
      <Progress {...args} />
    </div>
  ),
}

export const Empty: Story = {
  args: {
    value: 0,
  },
  render: (args) => (
    <div className="w-80">
      <Progress {...args} />
    </div>
  ),
}

export const Complete: Story = {
  args: {
    value: 100,
  },
  render: (args) => (
    <div className="w-80">
      <Progress {...args} />
    </div>
  ),
}

export const Animated: Story = {
  render: () => {
    const [progress, setProgress] = useState(0)

    useEffect(() => {
      const timer = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) return 0
          return prev + 10
        })
      }, 500)

      return () => clearInterval(timer)
    }, [])

    return (
      <div className="w-80 space-y-2">
        <Progress value={progress} />
        <p className="text-sm text-center text-muted-foreground">{progress}%</p>
      </div>
    )
  },
}
