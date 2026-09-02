import { useEffect, useState } from 'react'
import { X, Play, Clock, HardDrive, AlertCircle } from 'lucide-react'
import { supabase } from '../lib/supabase'

interface Recording {
  id: string
  device_id: string
  filename: string
  start_time: string
  end_time: string
  file_size: number
  created_at: string
}

interface RecordingsListProps {
  deviceId: string
  deviceName: string
  onClose: () => void
}

export default function RecordingsList({ deviceId, deviceName, onClose }: RecordingsListProps) {
  const [recordings, setRecordings] = useState<Recording[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [playingId, setPlayingId] = useState<string | null>(null)
  const [token, setToken] = useState<string>('')

  useEffect(() => {
    fetchRecordings()
  }, [deviceId])

  const fetchRecordings = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) return
      setToken(session.access_token)

      const response = await fetch(`http://localhost:8000/api/admin/recordings/${deviceId}`, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setRecordings(data)
      } else {
        setError('Failed to fetch recordings.')
      }
    } catch (err) {
      setError(String(err))
    } finally {
      setLoading(false)
    }
  }

  const formatSize = (bytes: number) => {
    const mb = bytes / (1024 * 1024)
    return `${mb.toFixed(2)} MB`
  }

  const formatDuration = (start: string, end: string) => {
    const ms = new Date(end).getTime() - new Date(start).getTime()
    const seconds = Math.round(ms / 1000)
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}m ${secs}s`
  }

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center bg-gray-50 rounded-t-lg">
          <h2 className="text-xl font-semibold text-gray-800">
            Recording History: {deviceName}
          </h2>
          <button 
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="mb-4 p-4 bg-red-50 text-red-700 rounded-md flex items-center gap-2">
              <AlertCircle size={20} />
              {error}
            </div>
          )}

          {loading ? (
            <div className="text-center text-gray-500 py-12">Loading recordings...</div>
          ) : (
            <div className="space-y-4">
              {recordings.length === 0 ? (
                <div className="text-center text-gray-500 py-12 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                  No recordings found for this device.
                </div>
              ) : (
                recordings.map(rec => (
                  <div key={rec.id} className="border border-gray-200 rounded-lg overflow-hidden">
                    <div className="p-4 bg-gray-50 flex justify-between items-center">
                      <div className="flex flex-col">
                        <span className="font-medium text-gray-900">
                          {new Date(rec.start_time).toLocaleString()}
                        </span>
                        <div className="flex items-center gap-4 text-sm text-gray-500 mt-1">
                          <span className="flex items-center gap-1">
                            <Clock size={14} />
                            {formatDuration(rec.start_time, rec.end_time)}
                          </span>
                          <span className="flex items-center gap-1">
                            <HardDrive size={14} />
                            {formatSize(rec.file_size)}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => setPlayingId(playingId === rec.id ? null : rec.id)}
                        className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
                      >
                        <Play size={16} className={playingId === rec.id ? "text-blue-600" : ""} />
                        {playingId === rec.id ? 'Close Player' : 'Play'}
                      </button>
                    </div>
                    
                    {playingId === rec.id && (
                      <div className="bg-black aspect-video flex items-center justify-center">
                        <video 
                          controls 
                          autoPlay 
                          className="w-full h-full"
                          src={`http://localhost:8000/api/admin/recordings/play/${rec.id}?token=${token}`}
                        >
                          Your browser does not support the video tag.
                        </video>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
