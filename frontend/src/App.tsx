import { useState, useEffect } from 'react'

function App() {
  const [health, setHealth] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => setError(err.message))
  }, [])

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-lg shadow-md p-8 max-w-md w-full">
        <h1 className="text-2xl font-bold text-gray-800 mb-6 text-center">
          Employee Monitor
        </h1>
        
        <div className="space-y-4">
          <div className="flex items-center justify-between p-4 bg-gray-50 rounded-md">
            <span className="font-semibold text-gray-700">Backend Status:</span>
            {error ? (
              <span className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm font-medium">
                Offline
              </span>
            ) : health ? (
              <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium">
                Online
              </span>
            ) : (
              <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                Connecting...
              </span>
            )}
          </div>

          {health && (
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-md">
              <span className="font-semibold text-gray-700">Database Status:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                health.database === 'ok' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
              }`}>
                {health.database === 'ok' ? 'Connected' : 'Error'}
              </span>
            </div>
          )}

          {error && (
            <div className="mt-4 p-3 bg-red-50 text-red-700 text-sm rounded border border-red-200">
              Error connecting to backend: {error}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
