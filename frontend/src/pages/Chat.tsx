import { useState } from 'react'
import { Send, Loader } from 'lucide-react'

export default function Chat() {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([
    {
      role: 'assistant',
      content: 'Genaryn AI Deputy Commander online. How can I assist you with your mission today?'
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setIsLoading(true)

    // TODO: Implement actual API call
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'I understand your request. Let me analyze the situation and provide recommendations...'
        }
      ])
      setIsLoading(false)
    }, 1000)
  }

  return (
    <div className="flex flex-col h-full max-h-[calc(100vh-12rem)]">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-white mb-2">AI Deputy Commander</h1>
        <p className="text-gray-400">Strategic advisor for military operations</p>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto bg-gray-800 border border-gray-700 rounded-lg p-6 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={
                message.role === 'user'
                  ? 'message-user'
                  : 'message-assistant'
              }
            >
              {message.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="message-assistant flex items-center space-x-2">
              <Loader className="w-4 h-4 animate-spin" />
              <span>Analyzing...</span>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="mt-4 flex space-x-4">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Enter your message..."
          className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-400 focus:outline-none focus:border-primary-500"
          disabled={isLoading}
        />
        <button
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          className="btn-military px-6 flex items-center space-x-2"
        >
          <Send className="w-4 h-4" />
          <span>Send</span>
        </button>
      </div>
    </div>
  )
}