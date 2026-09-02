import { useEffect, useRef, useState } from 'react'
import { X, AlertCircle } from 'lucide-react'
import { supabase } from '../lib/supabase'

interface LiveViewProps {
  deviceId: string
  deviceName: string
  onClose: () => void
}

export default function LiveView({ deviceId, deviceName, onClose }: LiveViewProps) {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'error'>('connecting')
  const imgRef = useRef<HTMLImageElement>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    let ws: WebSocket
    
    const connect = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) return

      const wsUrl = `ws://localhost:8000/api/ws/admin/${deviceId}?token=${session.access_token}`
      ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setStatus('connected')
      }

      ws.onmessage = (event) => {
        // Event data is a Blob because the agent sends binary frames
        if (event.data instanceof Blob && imgRef.current) {
          const url = URL.createObjectURL(event.data)
          // Clean up old object URL to prevent memory leaks
          if (imgRef.current.src) {
            URL.revokeObjectURL(imgRef.current.src)
          }
          imgRef.current.src = url
        }
      }

      ws.onerror = () => {
        setStatus('error')
      }

      ws.onclose = () => {
        setStatus('error')
      }
    }

    connect()

    return () => {
      if (wsRef.current) {
        wsRef.current.close()
      }
      if (imgRef.current?.src) {
        URL.revokeObjectURL(imgRef.current.src)
      }
    }
  }, [deviceId])

  return (
    <div className="fixed inset-0 bg-black/80 z-50 flex flex-col">
      {/* Header */}
      <div className="bg-gray-900 text-white p-4 flex justify-between items-center">
        <div>
          <h2 className="text-lg font-semibold">{deviceName} - Live Screen</h2>
          <div className="flex items-center gap-2 text-sm mt-1">
            {status === 'connecting' && <span className="text-yellow-400">Connecting...</span>}
            {status === 'connected' && (
              <>
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                <span className="text-gray-300">Live</span>
              </>
            )}
            {status === 'error' && (
              <span className="text-red-400 flex items-center gap-1">
                <AlertCircle size={14} /> Connection lost
              </span>
            )}
          </div>
        </div>
        <button 
          onClick={onClose}
          className="p-2 hover:bg-gray-800 rounded-full transition-colors text-gray-400 hover:text-white flex items-center gap-2"
        >
          <span className="text-sm font-medium">Stop Viewing</span>
          <X size={24} />
        </button>
      </div>

      {/* Screen Area */}
      <div className="flex-1 p-4 flex items-center justify-center overflow-hidden relative">
        {status === 'connecting' && (
          <div className="text-white text-lg animate-pulse">Waiting for stream...</div>
        )}
        <img 
          ref={imgRef}
          alt={`Live feed of ${deviceName}`}
          className="max-h-full max-w-full object-contain bg-black shadow-2xl"
          style={{ display: status === 'connected' ? 'block' : 'none' }}
        />
      </div>
    </div>
  )
}
