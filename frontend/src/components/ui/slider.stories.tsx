/**
 * Storybook stories for Slider component.
 */
import type { Meta, StoryObj } from '@storybook/react-vite'
import { useState } from 'react'
import { Slider } from './slider'
import { Label } from './label'

const meta = {
  title: 'UI/Slider',
  component: Slider,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Slider>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => {
    const [value, setValue] = useState([50])
    return (
      <div className="w-80 space-y-4">
        <div className="flex items-center justify-between">
          <Label>Volume</Label>
          <span className="text-sm text-muted-foreground">{value[0]}%</span>
        </div>
        <Slider value={value} onValueChange={setValue} max={100} step={1} />
      </div>
    )
  },
}

export const Range: Story = {
  render: () => {
    const [value, setValue] = useState([25, 75])
    return (
      <div className="w-80 space-y-4">
        <div className="flex items-center justify-between">
          <Label>Price Range</Label>
          <span className="text-sm text-muted-foreground">
            ${value[0]} - ${value[1]}
          </span>
        </div>
        <Slider value={value} onValueChange={setValue} max={100} step={1} />
      </div>
    )
  },
}

export const Disabled: Story = {
  render: () => (
    <div className="w-80 space-y-4">
      <Label>Disabled Slider</Label>
      <Slider value={[50]} max={100} step={1} disabled />
    </div>
  ),
}
