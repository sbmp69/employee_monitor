import { useState } from 'react'
import { X, ShieldAlert, CheckCircle, XCircle, AlertCircle, Clock } from 'lucide-react'
import { supabase } from '../lib/supabase'

interface PolicyModalProps {
  deviceId: string
  deviceName: string
  initialWebsites: string[]
  policyStatus: string | null
  onClose: () => void
  onSaved: () => void
}

export default function PolicyModal({ deviceId, deviceName, initialWebsites, policyStatus, onClose, onSaved }: PolicyModalProps) {
  const [websitesText, setWebsitesText] = useState(initialWebsites.join('\n'))
  const [saving, setSaving] = useState(false)

  const handleSave = async () => {
    setSaving(true)
    const websites = websitesText.split('\n').map(s => s.trim()).filter(s => s.length > 0)
    
    try {
      const { data: { session } } = await supabase.auth.getSession()
      if (!session) return

      const response = await fetch(`http://localhost:8000/api/admin/computers/${deviceId}/policy`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ websites })
      })
      
      if (response.ok) {
        onSaved()
      } else {
        alert("Failed to save policy")
      }
    } catch (e) {
      alert("Error saving policy")
    } finally {
      setSaving(false)
    }
  }

  const renderStatus = () => {
    if (!policyStatus || policyStatus === 'Unconfigured') {
      return (
        <span className="flex items-center gap-1 text-gray-500">
          <AlertCircle size={14} /> Unconfigured
        </span>
      )
    }
    if (policyStatus.toLowerCase().includes('success')) {
      return (
        <span className="flex items-center gap-1 text-green-600">
          <CheckCircle size={14} /> {policyStatus}
        </span>
      )
    }
    if (policyStatus.toLowerCase().includes('pushing') || policyStatus.toLowerCase().includes('pending')) {
      return (
        <span className="flex items-center gap-1 text-blue-600 animate-pulse">
          <Clock size={14} /> {policyStatus}
        </span>
      )
    }
    return (
      <span className="flex items-center gap-1 text-red-600">
        <XCircle size={14} /> {policyStatus}
      </span>
    )
  }

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg">
        <div className="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
          <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
            <ShieldAlert className="text-indigo-600" />
            Website Restrictions
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <X size={24} />
          </button>
        </div>

        <div className="p-6">
          <p className="text-sm text-gray-600 mb-4">
            Enter the domains you want to block on <strong>{deviceName}</strong>, one per line. 
            (e.g. <code>youtube.com</code>, <code>facebook.com</code>)
          </p>

          <textarea
            value={websitesText}
            onChange={(e) => setWebsitesText(e.target.value)}
            className="w-full h-48 p-3 border border-gray-300 rounded-md focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="reddit.com&#10;twitter.com"
          />

          <div className="mt-4 p-3 bg-gray-50 rounded border border-gray-200 text-sm">
            <div className="font-semibold text-gray-700 mb-1">Agent Status:</div>
            {renderStatus()}
          </div>

          <div className="mt-4 text-xs text-gray-500">
            <strong>Note:</strong> The agent must be running with Administrator privileges to apply these rules.
          </div>
        </div>

        <div className="px-6 py-4 border-t border-gray-200 flex justify-end gap-3 bg-gray-50 rounded-b-lg">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Apply Policy'}
          </button>
        </div>
      </div>
    </div>
  )
}
