import { Shield, Users, MessageSquare, AlertTriangle, TrendingUp, Clock } from 'lucide-react'
import { motion } from 'framer-motion'

export default function Dashboard() {
  const stats = [
    { label: 'Active Missions', value: '3', icon: Shield, color: 'text-primary-500' },
    { label: 'Personnel', value: '147', icon: Users, color: 'text-green-500' },
    { label: 'Messages Today', value: '42', icon: MessageSquare, color: 'text-blue-500' },
    { label: 'Alerts', value: '2', icon: AlertTriangle, color: 'text-yellow-500' },
  ]

  const recentDecisions = [
    { id: 1, title: 'Resource Allocation Alpha', status: 'approved', time: '2 hours ago', priority: 'high' },
    { id: 2, title: 'Patrol Route Optimization', status: 'pending', time: '4 hours ago', priority: 'medium' },
    { id: 3, title: 'Supply Chain Adjustment', status: 'executed', time: '6 hours ago', priority: 'low' },
  ]

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Command Dashboard</h1>
        <p className="text-gray-400">Real-time operational overview and metrics</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        {stats.map((stat, index) => {
          const Icon = stat.icon
          return (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="bg-gray-800 border border-gray-700 rounded-lg p-6"
            >
              <div className="flex items-center justify-between mb-4">
                <Icon className={`w-8 h-8 ${stat.color}`} />
                <TrendingUp className="w-4 h-4 text-green-500" />
              </div>
              <p className="text-3xl font-bold text-white mb-1">{stat.value}</p>
              <p className="text-sm text-gray-400">{stat.label}</p>
            </motion.div>
          )
        })}
      </div>

      {/* Recent Decisions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="bg-gray-800 border border-gray-700 rounded-lg p-6"
      >
        <h2 className="text-xl font-semibold text-white mb-4">Recent Decisions</h2>
        <div className="space-y-4">
          {recentDecisions.map((decision) => (
            <div
              key={decision.id}
              className="flex items-center justify-between p-4 bg-gray-900 rounded-lg"
            >
              <div className="flex-1">
                <h3 className="font-medium text-white">{decision.title}</h3>
                <div className="flex items-center space-x-4 mt-2">
                  <span
                    className={clsx('text-xs font-medium px-2 py-1 rounded', {
                      'bg-green-900 text-green-300': decision.status === 'approved',
                      'bg-yellow-900 text-yellow-300': decision.status === 'pending',
                      'bg-blue-900 text-blue-300': decision.status === 'executed',
                    })}
                  >
                    {decision.status.toUpperCase()}
                  </span>
                  <span
                    className={clsx('text-xs font-medium px-2 py-1 rounded', {
                      'risk-high': decision.priority === 'high',
                      'risk-moderate': decision.priority === 'medium',
                      'risk-low': decision.priority === 'low',
                    })}
                  >
                    {decision.priority.toUpperCase()} PRIORITY
                  </span>
                </div>
              </div>
              <div className="flex items-center text-gray-400 text-sm">
                <Clock className="w-4 h-4 mr-1" />
                {decision.time}
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* System Status */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="mt-6 bg-gray-800 border border-gray-700 rounded-lg p-6"
      >
        <h2 className="text-xl font-semibold text-white mb-4">System Status</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="flex items-center space-x-3">
            <div className="status-indicator status-online"></div>
            <span className="text-gray-300">AI Deputy: Operational</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="status-indicator status-online"></div>
            <span className="text-gray-300">Database: Connected</span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="status-indicator status-online"></div>
            <span className="text-gray-300">LLM Service: Ready</span>
          </div>
        </div>
      </motion.div>
    </div>
  )
}

function clsx(...classes: (string | boolean | undefined | null | { [key: string]: boolean })[]): string {
  return classes
    .filter(Boolean)
    .map((cls) => {
      if (typeof cls === 'string') return cls
      if (typeof cls === 'object' && cls !== null) {
        return Object.keys(cls)
          .filter((key) => cls[key])
          .join(' ')
      }
      return ''
    })
    .join(' ')
}