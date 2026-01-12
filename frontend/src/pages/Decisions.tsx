import { BarChart3, TrendingUp, AlertTriangle, CheckCircle } from 'lucide-react'

export default function Decisions() {
  const decisions = [
    {
      id: 1,
      title: 'Operation Red Dawn - Resource Allocation',
      type: 'tactical',
      status: 'pending',
      priority: 'high',
      confidence: 0.87,
      created: '2024-01-12T10:00:00Z',
      courses: [
        { name: 'COA 1: Full deployment', risk: 'moderate', success: 0.75 },
        { name: 'COA 2: Phased approach', risk: 'low', success: 0.65 },
        { name: 'COA 3: Minimal footprint', risk: 'high', success: 0.45 },
      ],
    },
    {
      id: 2,
      title: 'Supply Route Security Enhancement',
      type: 'operational',
      status: 'approved',
      priority: 'medium',
      confidence: 0.92,
      created: '2024-01-11T14:30:00Z',
      courses: [
        { name: 'COA 1: Convoy protection', risk: 'low', success: 0.85 },
        { name: 'COA 2: Alternate routes', risk: 'moderate', success: 0.70 },
      ],
    },
  ]

  return (
    <div>
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2">Decision Analysis</h1>
        <p className="text-gray-400">Military decision support and course of action analysis</p>
      </div>

      {/* Decision Cards */}
      <div className="space-y-6">
        {decisions.map((decision) => (
          <div key={decision.id} className="decision-card">
            {/* Decision Header */}
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-xl font-semibold text-white mb-2">{decision.title}</h2>
                <div className="flex items-center space-x-4">
                  <span className={`text-xs font-medium px-2 py-1 rounded uppercase ${
                    decision.type === 'tactical' ? 'bg-blue-900 text-blue-300' :
                    decision.type === 'operational' ? 'bg-purple-900 text-purple-300' :
                    'bg-gray-700 text-gray-300'
                  }`}>
                    {decision.type}
                  </span>
                  <span className={`risk-${decision.priority}`}>
                    {decision.priority.toUpperCase()} PRIORITY
                  </span>
                  <span className={`text-xs font-medium px-2 py-1 rounded ${
                    decision.status === 'pending' ? 'bg-yellow-900 text-yellow-300' :
                    decision.status === 'approved' ? 'bg-green-900 text-green-300' :
                    'bg-gray-700 text-gray-300'
                  }`}>
                    {decision.status.toUpperCase()}
                  </span>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-400">AI Confidence</p>
                <p className="text-2xl font-bold text-primary-400">
                  {(decision.confidence * 100).toFixed(0)}%
                </p>
              </div>
            </div>

            {/* COA Analysis */}
            <div className="mt-6">
              <h3 className="text-lg font-medium text-white mb-3">Courses of Action</h3>
              <div className="space-y-3">
                {decision.courses.map((coa, index) => (
                  <div key={index} className="bg-gray-900 rounded-lg p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex-1">
                        <p className="font-medium text-white">{coa.name}</p>
                        <div className="flex items-center space-x-4 mt-2">
                          <span className={`risk-${coa.risk}`}>
                            Risk: {coa.risk.toUpperCase()}
                          </span>
                          <div className="flex items-center space-x-1">
                            <TrendingUp className="w-4 h-4 text-green-400" />
                            <span className="text-sm text-gray-400">
                              Success: {(coa.success * 100).toFixed(0)}%
                            </span>
                          </div>
                        </div>
                      </div>
                      {index === 0 && (
                        <div className="flex items-center space-x-2 text-primary-400">
                          <CheckCircle className="w-5 h-5" />
                          <span className="text-sm font-medium">RECOMMENDED</span>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Action Buttons */}
            <div className="mt-6 flex space-x-4">
              <button className="btn-military">
                View Full Analysis
              </button>
              <button className="px-4 py-2 bg-gray-700 text-white font-medium rounded-md hover:bg-gray-600 transition-colors">
                Export Report
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}