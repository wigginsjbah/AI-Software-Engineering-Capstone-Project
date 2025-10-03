import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';

/**
 * Chat Interface Component
 * AI-Generated with glassmorphism design for business intelligence queries
 * 
 * This component was generated using AI assistance with the prompt:
 * "Create a React chat interface component with real-time messaging,
 * glassmorphism design, typing indicators, and integration with FastAPI backend
 * for business intelligence queries using RAG and OpenAI"
 */

const ChatInterface = ({ currentCompany, apiBase }) => {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId] = useState(() => 
    `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  );
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Add welcome message when component mounts
    if (messages.length === 0) {
      const welcomeMessage = {
        id: 'welcome',
        type: 'assistant',
        content: currentCompany 
          ? `Welcome! I'm your AI business intelligence assistant for ${currentCompany.name || currentCompany.company_id}. Ask me anything about your business data, trends, or performance metrics.`
          : 'Welcome! Please select or create a company first to start analyzing business data.',
        timestamp: new Date(),
        sources: []
      };
      setMessages([welcomeMessage]);
    }
  }, [currentCompany, messages.length]);

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    if (!currentCompany) {
      alert('Please select a company first to analyze business data.');
      return;
    }

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${apiBase}/api/v1/chat/`, {
        message: inputMessage,
        conversation_id: conversationId,
        company_id: currentCompany.company_id
      });

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: response.data.response || 'I received your message but couldn\'t generate a proper response.',
        timestamp: new Date(),
        sources: response.data.sources || [],
        queryType: response.data.query_type || 'general'
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const exampleQuestions = [
    "What are our top-selling products?",
    "Show me monthly revenue trends",
    "Which customers have the highest lifetime value?",
    "What are our inventory levels?",
    "How do our sales compare to industry benchmarks?"
  ];

  const handleExampleClick = (question) => {
    setInputMessage(question);
  };

  const formatMessage = (content) => {
    // Simple formatting for better readability
    return content.split('\n').map((line, index) => (
      <p key={index} className="mb-2 last:mb-0">
        {line}
      </p>
    ));
  };

  return (
    <div className="max-w-4xl mx-auto h-[calc(100vh-180px)]">
      <div className="glass-card h-full flex flex-col">
        {/* Chat Header */}
        <div className="border-b border-white/20 p-4">
          <h2 className="text-xl font-semibold text-gray-800">
            AI Business Intelligence Assistant
          </h2>
          {currentCompany && (
            <p className="text-sm text-gray-600 mt-1">
              Analyzing data for: <span className="font-medium">{currentCompany.name || currentCompany.company_id}</span>
            </p>
          )}
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-3xl rounded-lg p-4 ${
                  message.type === 'user'
                    ? 'bg-indigo-500 text-white'
                    : message.type === 'error'
                    ? 'bg-red-100 text-red-800 border border-red-200'
                    : 'bg-white/50 text-gray-800 border border-white/20'
                }`}
              >
                <div className="whitespace-pre-wrap">
                  {formatMessage(message.content)}
                </div>
                
                {/* Sources */}
                {message.sources && message.sources.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-xs font-medium text-gray-600 mb-2">Sources:</p>
                    <div className="space-y-1">
                      {message.sources.map((source, index) => (
                        <div key={index} className="text-xs text-gray-500">
                          📊 {source}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                <div className="text-xs text-gray-500 mt-2">
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white/50 border border-white/20 rounded-lg p-4">
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-indigo-500"></div>
                  <span className="text-gray-600">AI is thinking...</span>
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Example Questions */}
        {messages.length <= 1 && (
          <div className="border-t border-white/20 p-4">
            <p className="text-sm font-medium text-gray-700 mb-3">Try asking:</p>
            <div className="flex flex-wrap gap-2">
              {exampleQuestions.map((question, index) => (
                <button
                  key={index}
                  onClick={() => handleExampleClick(question)}
                  className="text-xs bg-white/30 hover:bg-white/50 text-gray-700 px-3 py-2 rounded-full transition-colors duration-200 border border-white/20"
                >
                  {question}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Input Area */}
        <div className="border-t border-white/20 p-4">
          <div className="flex space-x-3">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={
                currentCompany 
                  ? "Ask me anything about your business data..." 
                  : "Please select a company first..."
              }
              className="flex-1 resize-none border border-white/20 rounded-lg px-4 py-3 bg-white/50 text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
              rows="2"
              disabled={!currentCompany || isLoading}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || !currentCompany || isLoading}
              className="px-6 py-3 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 font-medium"
            >
              Send
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;