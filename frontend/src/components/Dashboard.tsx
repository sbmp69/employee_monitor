import { useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { LogOut, Monitor, Clock, Play, Video, Square, History, ShieldAlert } from 'lucide-react'
import LiveView from './LiveView'
import RecordingsList from './RecordingsList'
import PolicyModal from './PolicyModal'

interface Computer {
  id: string
  device_name: string
  employee_name: string | null
  status: string
  last_seen: string
  agent_version: string | null
  blocked_websites: string[]
  policy_status: string | null
}

interface DashboardProps {
  onLogout: () => void
}

export default function Dashboard({ onLogout }: DashboardProps) {
  const [computers, setComputers] = useState<Computer[]>([])
  const [loading, setLoading] = useState(true)
  const [viewingDevice, setViewingDevice] = useState<Computer | null>(null)
  const [historyDevice, setHistoryDevice] = useState<Computer | null>(null)
  const [policyDevice, setPolicyDevice] = useState<Computer | null>(null)
  const [recordingDevices, setRecordingDevices] = useState<Set<string>>(new Set())

  useEffect(() => {
    fetchComputers()
    const interval = setInterval(fetchComputers, 10000)
    return () => clearInterval(interval)
  }, [])

  const fetchComputers = async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) return

      const response = await fetch('http://localhost:8000/api/admin/computers', {
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      })
      if (response.ok) {
        const data = await response.json()
        setComputers(data)
      }
    } catch (error) {
      console.error('Failed to fetch computers:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = async () => {
    await supabase.auth.signOut()
    onLogout()
  }

  const toggleRecording = async (deviceId: string, isRecording: boolean) => {
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) return

      const endpoint = isRecording ? 'stop' : 'start'
      const response = await fetch(`http://localhost:8000/api/admin/recordings/${endpoint}/${deviceId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      })
      
      if (response.ok) {
        setRecordingDevices(prev => {
          const next = new Set(prev)
          if (isRecording) {
            next.delete(deviceId)
          } else {
            next.add(deviceId)
          }
          return next
        })
      } else {
        alert('Failed to send recording command.')
      }
    } catch (err) {
      alert('Error communicating with backend.')
    }
  }

  const isOnline = (lastSeen: string, status: string) => {
    if (status !== 'online') return false
    const lastSeenDate = new Date(lastSeen)
    const now = new Date()
    const diffSeconds = (now.getTime() - lastSeenDate.getTime()) / 1000
    return diffSeconds < 90
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Monitor className="text-blue-600" />
            Employee Monitor Dashboard
          </h1>
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            <LogOut size={16} />
            Logout
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="px-4 py-5 border-b border-gray-200 sm:px-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900">Registered Computers</h3>
          </div>
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading...</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Device Name</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Employee</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Seen</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {computers.map((pc) => {
                    const online = isOnline(pc.last_seen, pc.status)
                    const isRecording = recordingDevices.has(pc.id)
                    return (
                      <tr key={pc.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {pc.device_name}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                          {pc.employee_name || 'Unassigned'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap">
                          <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${
                            online ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                          }`}>
                            {online ? 'Online' : 'Offline'}
                          </span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 flex items-center gap-1">
                          <Clock size={14} />
                          {new Date(pc.last_seen).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => setViewingDevice(pc)}
                              disabled={!online}
                              className={`flex items-center gap-1 px-3 py-1.5 rounded-md transition-colors ${
                                online 
                                  ? 'bg-blue-50 text-blue-700 hover:bg-blue-100' 
                                  : 'bg-gray-50 text-gray-400 cursor-not-allowed'
                              }`}
                              title="Live View"
                            >
                              <Play size={14} />
                              Live
                            </button>
                            
                            <button
                              onClick={() => toggleRecording(pc.id, isRecording)}
                              disabled={!online}
                              className={`flex items-center gap-1 px-3 py-1.5 rounded-md transition-colors ${
                                !online ? 'bg-gray-50 text-gray-400 cursor-not-allowed' :
                                isRecording 
                                  ? 'bg-red-50 text-red-700 hover:bg-red-100 animate-pulse'
                                  : 'bg-indigo-50 text-indigo-700 hover:bg-indigo-100'
                              }`}
                              title={isRecording ? "Stop Recording" : "Start Recording"}
                            >
                              {isRecording ? <Square size={14} /> : <Video size={14} />}
                              Rec
                            </button>

                            <button
                              onClick={() => setPolicyDevice(pc)}
                              className="flex items-center gap-1 px-3 py-1.5 rounded-md transition-colors bg-purple-50 text-purple-700 hover:bg-purple-100"
                              title="Set Policy"
                            >
                              <ShieldAlert size={14} />
                              Policy
                            </button>

                            <button
                              onClick={() => setHistoryDevice(pc)}
                              className="flex items-center gap-1 px-3 py-1.5 rounded-md transition-colors bg-gray-100 text-gray-700 hover:bg-gray-200"
                              title="View History"
                            >
                              <History size={14} />
                              History
                            </button>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                  {computers.length === 0 && (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                        No computers registered yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {viewingDevice && (
        <LiveView
          deviceId={viewingDevice.id}
          deviceName={viewingDevice.device_name}
          onClose={() => setViewingDevice(null)}
        />
      )}

      {historyDevice && (
        <RecordingsList
          deviceId={historyDevice.id}
          deviceName={historyDevice.device_name}
          onClose={() => setHistoryDevice(null)}
        />
      )}

      {policyDevice && (
        <PolicyModal
          deviceId={policyDevice.id}
          deviceName={policyDevice.device_name}
          initialWebsites={policyDevice.blocked_websites || []}
          policyStatus={policyDevice.policy_status}
          onClose={() => setPolicyDevice(null)}
          onSaved={() => {
            setPolicyDevice(null)
            fetchComputers()
          }}
        />
      )}
    </div>
  )
}
