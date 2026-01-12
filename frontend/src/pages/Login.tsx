import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Shield, Lock, User } from 'lucide-react'

export default function Login() {
  const navigate = useNavigate()
  const [credentials, setCredentials] = useState({ username: '', password: '' })
  const [isLoading, setIsLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    // TODO: Implement actual authentication
    setTimeout(() => {
      navigate('/')
    }, 1000)
  }

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center tactical-grid">
      <div className="bg-gray-950 border border-gray-700 rounded-lg p-8 w-full max-w-md">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <Shield className="w-16 h-16 text-primary-500 mb-4" />
          <h1 className="text-2xl font-bold text-white">Genaryn AI Deputy</h1>
          <p className="text-sm text-gray-400 mt-2">Independent AI Judgment. Stronger Commander Decisions.</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Username / Email
            </label>
            <div className="relative">
              <User className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={credentials.username}
                onChange={(e) => setCredentials({ ...credentials, username: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-11 pr-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-primary-500"
                placeholder="Enter your username"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Password
            </label>
            <div className="relative">
              <Lock className="absolute left-3 top-3.5 w-5 h-5 text-gray-400" />
              <input
                type="password"
                value={credentials.password}
                onChange={(e) => setCredentials({ ...credentials, password: e.target.value })}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg pl-11 pr-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-primary-500"
                placeholder="Enter your password"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full btn-military py-3 text-center"
          >
            {isLoading ? 'Authenticating...' : 'Login to Command Center'}
          </button>
        </form>

        {/* Security Notice */}
        <div className="mt-8 p-4 bg-gray-800 border border-gray-700 rounded-lg">
          <p className="text-xs text-gray-400 text-center">
            This is a secure military system. Unauthorized access is prohibited and will be prosecuted.
            All activities are monitored and logged.
          </p>
        </div>
      </div>
    </div>
  )
}