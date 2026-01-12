import { Shield } from 'lucide-react'

export default function LoadingScreen() {
  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center">
      <div className="text-center">
        <Shield className="w-16 h-16 text-primary-500 mx-auto animate-pulse" />
        <h2 className="mt-4 text-xl font-semibold text-white">Loading...</h2>
        <p className="mt-2 text-gray-400">Initializing Genaryn AI Deputy Commander</p>
        <div className="mt-8 flex justify-center space-x-2">
          <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  )
}