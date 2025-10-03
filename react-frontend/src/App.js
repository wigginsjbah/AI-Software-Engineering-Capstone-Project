import React, { useState, useEffect } from 'react';
import axios from 'axios';
import ChatInterface from './components/ChatInterface';
import CompanyManager from './components/CompanyManager';
import DatabaseViewer from './components/DatabaseViewer';
import Navigation from './components/Navigation';
import './App.css';

/**
 * Main React Application Component
 * AI-Generated for Capstone Project Deliverables
 * 
 * This component was generated using the following AI prompt:
 * "Create a modern React application for a business intelligence platform with:
 * 1. Chat interface for natural language business queries
 * 2. Company management dashboard
 * 3. Database viewer and analytics
 * 4. Modern glassmorphism design with Tailwind CSS
 * 5. Integration with FastAPI backend
 * 6. State management for current company and user data"
 */

function App() {
  const [currentView, setCurrentView] = useState('chat');
  const [currentCompany, setCurrentCompany] = useState(null);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // API base URL - connects to FastAPI backend
  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8010';

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      
      // Fetch companies list
      const companiesResponse = await axios.get(`${API_BASE}/api/companies/`);
      setCompanies(companiesResponse.data);

      // Fetch current company
      try {
        const currentResponse = await axios.get(`${API_BASE}/api/companies/current`);
        setCurrentCompany(currentResponse.data);
      } catch (err) {
        // No current company set - this is fine
        console.log('No current company set');
      }

    } catch (err) {
      setError('Failed to load initial data');
      console.error('Error fetching initial data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCompanySwitch = async (companyId) => {
    try {
      const response = await axios.post(`${API_BASE}/api/companies/${companyId}/switch`);
      setCurrentCompany(response.data);
      
      // Refresh companies list
      await fetchInitialData();
    } catch (err) {
      setError('Failed to switch company');
      console.error('Error switching company:', err);
    }
  };

  const renderContent = () => {
    switch (currentView) {
      case 'chat':
        return (
          <ChatInterface 
            currentCompany={currentCompany}
            apiBase={API_BASE}
          />
        );
      case 'companies':
        return (
          <CompanyManager 
            companies={companies}
            currentCompany={currentCompany}
            onCompanySwitch={handleCompanySwitch}
            onCompanyCreated={fetchInitialData}
            apiBase={API_BASE}
          />
        );
      case 'database':
        return (
          <DatabaseViewer 
            currentCompany={currentCompany}
            apiBase={API_BASE}
          />
        );
      default:
        return <ChatInterface currentCompany={currentCompany} apiBase={API_BASE} />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 flex items-center justify-center">
        <div className="glass-card p-8 text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading AI Business Intelligence Platform...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Navigation */}
      <Navigation 
        currentView={currentView}
        onViewChange={setCurrentView}
        currentCompany={currentCompany}
      />

      {/* Error Message */}
      {error && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-4 mx-4">
          <p className="font-medium">Error</p>
          <p>{error}</p>
          <button 
            onClick={() => setError(null)}
            className="text-red-500 hover:text-red-700 underline text-sm mt-2"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {renderContent()}
      </main>

      {/* Footer */}
      <footer className="text-center py-6 text-gray-500 text-sm">
        <p>AI-Powered Business Intelligence Platform | Capstone Project 2025</p>
        <p className="mt-1">Built with React, FastAPI, and OpenAI GPT-4</p>
      </footer>
    </div>
  );
}

export default App;