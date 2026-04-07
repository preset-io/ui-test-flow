import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import type { Screenshot } from '@/types'
import { formatDate } from '@/lib/utils'

interface ScreenshotGalleryProps {
  screenshots: Screenshot[]
}

export function ScreenshotGallery({ screenshots }: ScreenshotGalleryProps) {
  const [selectedIndex, setSelectedIndex] = useState<number | null>(null)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Screenshots ({screenshots.length})</CardTitle>
      </CardHeader>
      <CardContent>
        {screenshots.length === 0 ? (
          <p className="text-sm text-muted-foreground text-center py-8">
            No screenshots captured
          </p>
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {screenshots.map((screenshot, index) => (
              <div
                key={screenshot.id}
                className="group relative cursor-pointer rounded-lg overflow-hidden border hover:border-primary transition-colors"
                onClick={() => setSelectedIndex(index)}
              >
                <img
                  src={screenshot.thumbnail_url || screenshot.url}
                  alt={screenshot.step_name}
                  className="w-full h-40 object-cover"
                />
                <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center text-white p-2">
                  <p className="text-sm font-medium text-center">
                    {screenshot.step_name}
                  </p>
                  <p className="text-xs text-gray-300">
                    Step {screenshot.step_index + 1}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        {selectedIndex !== null && (
          <div
            className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4"
            onClick={() => setSelectedIndex(null)}
          >
            <div className="relative max-w-5xl w-full">
              <img
                src={screenshots[selectedIndex].url}
                alt={screenshots[selectedIndex].step_name}
                className="w-full h-auto rounded-lg"
              />
              <div className="absolute bottom-4 left-4 right-4 bg-black/75 rounded p-4 text-white">
                <p className="font-medium">{screenshots[selectedIndex].step_name}</p>
                <p className="text-sm text-gray-300">
                  Step {screenshots[selectedIndex].step_index + 1} of {screenshots.length}
                </p>
                {screenshots[selectedIndex].timestamp && (
                  <p className="text-xs text-gray-400">
                    {formatDate(screenshots[selectedIndex].timestamp)}
                  </p>
                )}
              </div>
              <button
                className="absolute top-4 right-4 text-white bg-black/50 rounded-full p-2 hover:bg-black/75"
                onClick={() => setSelectedIndex(null)}
              >
                ✕
              </button>
              {selectedIndex > 0 && (
                <button
                  className="absolute left-4 top-1/2 -translate-y-1/2 text-white bg-black/50 rounded-full p-2 hover:bg-black/75"
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelectedIndex(selectedIndex - 1)
                  }}
                >
                  ←
                </button>
              )}
              {selectedIndex < screenshots.length - 1 && (
                <button
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-white bg-black/50 rounded-full p-2 hover:bg-black/75"
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelectedIndex(selectedIndex + 1)
                  }}
                >
                  →
                </button>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
