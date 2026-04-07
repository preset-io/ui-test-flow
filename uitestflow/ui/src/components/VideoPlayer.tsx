import { useState, useRef } from 'react'
import ReactPlayer from 'react-player'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize,
  SkipBack,
  SkipForward,
  Download,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface VideoPlayerProps {
  url: string
  title?: string
  className?: string
}

export function VideoPlayer({ url, title, className }: VideoPlayerProps) {
  const playerRef = useRef<ReactPlayer>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const [playing, setPlaying] = useState(false)
  const [volume, setVolume] = useState(0.8)
  const [muted, setMuted] = useState(false)
  const [played, setPlayed] = useState(0)
  const [duration, setDuration] = useState(0)
  const [seeking, setSeeking] = useState(false)
  const [playbackRate, setPlaybackRate] = useState(1)

  const handlePlayPause = () => {
    setPlaying(!playing)
  }

  const handleProgress = (state: { played: number; playedSeconds: number; loaded: number; loadedSeconds: number }) => {
    if (!seeking) {
      setPlayed(state.played)
    }
  }

  const handleSeekMouseDown = () => {
    setSeeking(true)
  }

  const handleSeekChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPlayed(parseFloat(e.target.value))
  }

  const handleSeekMouseUp = (e: React.MouseEvent<HTMLInputElement>) => {
    setSeeking(false)
    playerRef.current?.seekTo(parseFloat((e.target as HTMLInputElement).value))
  }

  const handleDuration = (duration: number) => {
    setDuration(duration)
  }

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newVolume = parseFloat(e.target.value)
    setVolume(newVolume)
    setMuted(newVolume === 0)
  }

  const toggleMute = () => {
    setMuted(!muted)
  }

  const handleSkipBackward = () => {
    playerRef.current?.seekTo(Math.max(0, played - 0.1))
  }

  const handleSkipForward = () => {
    playerRef.current?.seekTo(Math.min(1, played + 0.1))
  }

  const handleFullscreen = () => {
    if (containerRef.current) {
      if (document.fullscreenElement) {
        document.exitFullscreen()
      } else {
        containerRef.current.requestFullscreen()
      }
    }
  }

  const handleDownload = async () => {
    try {
      const response = await fetch(url)
      const blob = await response.blob()
      const downloadUrl = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = title ? `${title}.mp4` : 'video.mp4'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(downloadUrl)
    } catch (error) {
      console.error('Error downloading video:', error)
    }
  }

  const formatTime = (seconds: number) => {
    const date = new Date(seconds * 1000)
    const mm = date.getUTCMinutes()
    const ss = date.getUTCSeconds().toString().padStart(2, '0')
    return `${mm}:${ss}`
  }

  const playbackRates = [0.5, 0.75, 1, 1.25, 1.5, 2]

  return (
    <Card className={cn('overflow-hidden', className)}>
      <CardContent className="p-0">
        <div ref={containerRef} className="relative bg-black group">
          <div className="aspect-video">
            <ReactPlayer
              ref={playerRef}
              url={url}
              width="100%"
              height="100%"
              playing={playing}
              volume={volume}
              muted={muted}
              playbackRate={playbackRate}
              onProgress={handleProgress}
              onDuration={handleDuration}
              config={{
                file: {
                  attributes: {
                    controlsList: 'nodownload',
                  },
                },
              }}
            />
          </div>

          {/* Controls Overlay */}
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 opacity-0 group-hover:opacity-100 transition-opacity">
            {/* Progress Bar */}
            <div className="mb-4">
              <input
                type="range"
                min={0}
                max={0.999999}
                step="any"
                value={played}
                onMouseDown={handleSeekMouseDown}
                onChange={handleSeekChange}
                onMouseUp={handleSeekMouseUp}
                className="w-full h-1 bg-white/30 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-3 [&::-webkit-slider-thumb]:h-3 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white"
              />
              <div className="flex justify-between text-xs text-white mt-1">
                <span>{formatTime(duration * played)}</span>
                <span>{formatTime(duration)}</span>
              </div>
            </div>

            {/* Controls */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handlePlayPause}
                  className="text-white hover:bg-white/20"
                >
                  {playing ? (
                    <Pause className="h-5 w-5" />
                  ) : (
                    <Play className="h-5 w-5" />
                  )}
                </Button>

                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleSkipBackward}
                  className="text-white hover:bg-white/20"
                >
                  <SkipBack className="h-4 w-4" />
                </Button>

                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleSkipForward}
                  className="text-white hover:bg-white/20"
                >
                  <SkipForward className="h-4 w-4" />
                </Button>

                <div className="flex items-center gap-2 ml-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={toggleMute}
                    className="text-white hover:bg-white/20"
                  >
                    {muted ? (
                      <VolumeX className="h-4 w-4" />
                    ) : (
                      <Volume2 className="h-4 w-4" />
                    )}
                  </Button>
                  <input
                    type="range"
                    min={0}
                    max={1}
                    step={0.05}
                    value={muted ? 0 : volume}
                    onChange={handleVolumeChange}
                    className="w-20 h-1 bg-white/30 rounded-lg appearance-none cursor-pointer [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-2 [&::-webkit-slider-thumb]:h-2 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-white"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2">
                <select
                  value={playbackRate}
                  onChange={(e) => setPlaybackRate(parseFloat(e.target.value))}
                  className="bg-white/20 text-white text-xs rounded px-2 py-1 border-none outline-none cursor-pointer hover:bg-white/30"
                >
                  {playbackRates.map((rate) => (
                    <option key={rate} value={rate} className="bg-black">
                      {rate}x
                    </option>
                  ))}
                </select>

                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleDownload}
                  className="text-white hover:bg-white/20"
                >
                  <Download className="h-4 w-4" />
                </Button>

                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleFullscreen}
                  className="text-white hover:bg-white/20"
                >
                  <Maximize className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
