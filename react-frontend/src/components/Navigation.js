import React from 'react';

/**
 * Navigation Component
 * AI-Generated for modern glassmorphism design
 * 
 * Generated with prompt: "Create a React navigation component with glassmorphism styling,
 * responsive design, and smooth transitions for a business intelligence platform"
 */

const Navigation = ({ currentView, onViewChange, currentCompany }) => {
  const navItems = [
    { id: 'chat', label: 'AI Chat', icon: '💬' },
    { id: 'companies', label: 'Companies', icon: '🏢' },
    { id: 'database', label: 'Database', icon: '📊' }
  ];

  return (
    <nav className="glass-nav sticky top-0 z-50 backdrop-blur-md bg-white/20 border-b border-white/20">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo/Brand */}
          <div className="flex items-center space-x-3">
            <div className="text-2xl">🤖</div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                AI Business Intelligence
              </h1>
              <p className="text-xs text-gray-600 hidden sm:block">
                Capstone Project 2025
              </p>
            </div>
          </div>

          {/* Navigation Items */}
          <div className="flex items-center space-x-1">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={`nav-item px-4 py-2 rounded-lg transition-all duration-200 flex items-center space-x-2 ${
                  currentView === item.id
                    ? 'bg-white/30 text-indigo-700 shadow-md'
                    : 'text-gray-600 hover:bg-white/20 hover:text-indigo-600'
                }`}
              >
                <span className="text-lg">{item.icon}</span>
                <span className="hidden sm:inline font-medium">{item.label}</span>
              </button>
            ))}
          </div>

          {/* Current Company Indicator */}
          {currentCompany && (
            <div className="hidden md:flex items-center space-x-2 glass-card px-3 py-1">
              <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium text-gray-700">
                {currentCompany.name || currentCompany.company_id}
              </span>
            </div>
          )}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;