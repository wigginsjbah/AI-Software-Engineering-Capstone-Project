import React, { useState } from 'react';
import axios from 'axios';

/**
 * Company Manager Component
 * AI-Generated for company creation and management
 * 
 * Generated with prompt: "Create a React component for managing companies
 * with AI database generation, glassmorphism design, and form handling
 * that integrates with FastAPI backend for business intelligence platform"
 */

const CompanyManager = ({ companies, currentCompany, onCompanySwitch, onCompanyCreated, apiBase }) => {
  const [isCreating, setIsCreating] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [formData, setFormData] = useState({
    companyName: '',
    businessType: 'ecommerce',
    complexity: 'medium',
    description: ''
  });

  const businessTypes = [
    { value: 'ecommerce', label: 'E-commerce', description: 'Online retail, products, orders, customers' },
    { value: 'healthcare', label: 'Healthcare', description: 'Patients, appointments, medical records' },
    { value: 'finance', label: 'Finance', description: 'Accounts, transactions, investments' },
    { value: 'technology', label: 'Technology', description: 'Projects, developers, deployments' },
    { value: 'manufacturing', label: 'Manufacturing', description: 'Products, inventory, suppliers' },
    { value: 'retail', label: 'Retail', description: 'Stores, sales, inventory management' },
    { value: 'education', label: 'Education', description: 'Students, courses, instructors' },
    { value: 'hospitality', label: 'Hospitality', description: 'Reservations, guests, services' },
    { value: 'consulting', label: 'Consulting', description: 'Projects, clients, deliverables' },
    { value: 'custom', label: 'Custom', description: 'Define your own business requirements' }
  ];

  const complexityLevels = [
    { value: 'simple', label: 'Simple', description: '3-5 tables, basic operations' },
    { value: 'medium', label: 'Medium', description: '6-12 tables, standard relationships' },
    { value: 'complex', label: 'Complex', description: '13-25 tables, advanced tracking' },
    { value: 'enterprise', label: 'Enterprise', description: '25+ tables, full-scale operations' }
  ];

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleCreateCompany = async (e) => {
    e.preventDefault();
    setIsGenerating(true);

    try {
      const response = await axios.post(`${apiBase}/api/v1/database/generate`, {
        business_type: formData.businessType,
        complexity: formData.complexity,
        description: formData.description || `${formData.companyName} - ${formData.businessType} business`,
        company_name: formData.companyName
      });

      if (response.data) {
        // Company created successfully
        await onCompanyCreated();
        setIsCreating(false);
        setFormData({
          companyName: '',
          businessType: 'ecommerce',
          complexity: 'medium',
          description: ''
        });
      }
    } catch (error) {
      console.error('Error creating company:', error);
      alert('Failed to create company. Please check the console for details.');
    } finally {
      setIsGenerating(false);
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    try {
      return new Date(dateString).toLocaleDateString();
    } catch {
      return 'Unknown';
    }
  };

  const getBusinessTypeInfo = (type) => {
    const info = businessTypes.find(bt => bt.value === type);
    return info ? info.label : type;
  };

  const getComplexityInfo = (complexity) => {
    const info = complexityLevels.find(cl => cl.value === complexity);
    return info ? info.label : complexity;
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-800">Company Management</h2>
            <p className="text-gray-600 mt-1">Create and manage your business databases with AI</p>
          </div>
          <button
            onClick={() => setIsCreating(true)}
            className="px-6 py-3 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-colors duration-200 font-medium flex items-center space-x-2"
          >
            <span>➕</span>
            <span>Create New Company</span>
          </button>
        </div>
      </div>

      {/* Create Company Form */}
      {isCreating && (
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <h3 className="text-xl font-semibold text-gray-800">Create New Company Database</h3>
            <button
              onClick={() => setIsCreating(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleCreateCompany} className="space-y-6">
            {/* Company Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Company Name *
              </label>
              <input
                type="text"
                name="companyName"
                value={formData.companyName}
                onChange={handleInputChange}
                required
                className="w-full px-4 py-3 border border-white/20 rounded-lg bg-white/50 text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Enter your company name"
              />
            </div>

            {/* Business Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Business Type *
              </label>
              <select
                name="businessType"
                value={formData.businessType}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-white/20 rounded-lg bg-white/50 text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {businessTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label} - {type.description}
                  </option>
                ))}
              </select>
            </div>

            {/* Complexity Level */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Database Complexity *
              </label>
              <select
                name="complexity"
                value={formData.complexity}
                onChange={handleInputChange}
                className="w-full px-4 py-3 border border-white/20 rounded-lg bg-white/50 text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                {complexityLevels.map((level) => (
                  <option key={level.value} value={level.value}>
                    {level.label} - {level.description}
                  </option>
                ))}
              </select>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Business Description (Optional)
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows="3"
                className="w-full px-4 py-3 border border-white/20 rounded-lg bg-white/50 text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Describe your business operations, products, or special requirements..."
              />
            </div>

            {/* Submit Button */}
            <div className="flex space-x-4">
              <button
                type="submit"
                disabled={isGenerating}
                className="flex-1 px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 font-medium flex items-center justify-center space-x-2"
              >
                {isGenerating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Generating Database with AI...</span>
                  </>
                ) : (
                  <>
                    <span>🤖</span>
                    <span>Generate Database with AI</span>
                  </>
                )}
              </button>
              <button
                type="button"
                onClick={() => setIsCreating(false)}
                className="px-6 py-3 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors duration-200 font-medium"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Companies List */}
      <div className="glass-card p-6">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Your Companies</h3>
        
        {companies.length === 0 ? (
          <div className="text-center py-8">
            <p className="text-gray-500 mb-4">No companies created yet</p>
            <p className="text-sm text-gray-400">Create your first company to start analyzing business data</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {companies.map((company) => (
              <div
                key={company.company_id}
                className={`p-4 border rounded-lg transition-all duration-200 cursor-pointer ${
                  currentCompany && currentCompany.company_id === company.company_id
                    ? 'border-indigo-500 bg-indigo-50/50 shadow-md'
                    : 'border-white/20 bg-white/20 hover:bg-white/30'
                }`}
                onClick={() => onCompanySwitch(company.company_id)}
              >
                <div className="flex items-start justify-between mb-3">
                  <h4 className="font-semibold text-gray-800 truncate">
                    {company.name || company.company_id}
                  </h4>
                  {currentCompany && currentCompany.company_id === company.company_id && (
                    <span className="text-xs bg-green-500 text-white px-2 py-1 rounded-full">
                      Active
                    </span>
                  )}
                </div>
                
                <div className="space-y-2 text-sm text-gray-600">
                  <div className="flex items-center space-x-2">
                    <span>🏢</span>
                    <span>{getBusinessTypeInfo(company.business_type || 'unknown')}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span>📊</span>
                    <span>{getComplexityInfo(company.complexity || 'unknown')}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span>📅</span>
                    <span>{formatDate(company.created_at)}</span>
                  </div>
                  {company.table_count && (
                    <div className="flex items-center space-x-2">
                      <span>🗃️</span>
                      <span>{company.table_count} tables</span>
                    </div>
                  )}
                </div>
                
                {company.description && (
                  <p className="text-xs text-gray-500 mt-3 truncate">
                    {company.description}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default CompanyManager;