import React, { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * Database Viewer Component
 * AI-Generated for viewing and analyzing business data
 * 
 * Generated with prompt: "Create a React component for viewing database schemas,
 * tables, and sample data with modern UI design and API integration"
 */

const DatabaseViewer = ({ currentCompany, apiBase }) => {
  const [tables, setTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState(null);
  const [tableData, setTableData] = useState([]);
  const [tableSchema, setTableSchema] = useState([]);
  const [loading, setLoading] = useState(false);
  const [dataLoading, setDataLoading] = useState(false);

  useEffect(() => {
    if (currentCompany) {
      fetchTables();
    }
  }, [currentCompany]);

  const fetchTables = async () => {
    if (!currentCompany) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${apiBase}/api/v1/data/tables`, {
        params: { company_id: currentCompany.company_id }
      });
      setTables(response.data || []);
    } catch (error) {
      console.error('Error fetching tables:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchTableData = async (tableName) => {
    if (!currentCompany || !tableName) return;
    
    setDataLoading(true);
    try {
      // Fetch table data
      const dataResponse = await axios.get(`${apiBase}/api/v1/data/table/${tableName}`, {
        params: { 
          company_id: currentCompany.company_id,
          limit: 50 
        }
      });
      setTableData(dataResponse.data || []);

      // Fetch table schema
      const schemaResponse = await axios.get(`${apiBase}/api/v1/data/table/${tableName}/schema`, {
        params: { company_id: currentCompany.company_id }
      });
      setTableSchema(schemaResponse.data || []);
      
    } catch (error) {
      console.error('Error fetching table data:', error);
      setTableData([]);
      setTableSchema([]);
    } finally {
      setDataLoading(false);
    }
  };

  const handleTableSelect = (tableName) => {
    setSelectedTable(tableName);
    fetchTableData(tableName);
  };

  const formatValue = (value) => {
    if (value === null || value === undefined) return '—';
    if (typeof value === 'string' && value.length > 50) {
      return value.substring(0, 50) + '...';
    }
    return String(value);
  };

  const getColumnType = (columnName) => {
    const column = tableSchema.find(col => col.name === columnName);
    return column ? column.type : 'TEXT';
  };

  if (!currentCompany) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="glass-card p-8 text-center">
          <div className="text-gray-500 mb-4">
            <span className="text-4xl">🏢</span>
          </div>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No Company Selected</h3>
          <p className="text-gray-600">Please select or create a company to view its database.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="glass-card p-6">
        <h2 className="text-2xl font-bold text-gray-800 mb-2">Database Viewer</h2>
        <p className="text-gray-600">
          Exploring: <span className="font-medium">{currentCompany.name || currentCompany.company_id}</span>
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Tables Sidebar */}
        <div className="lg:col-span-1">
          <div className="glass-card p-4">
            <h3 className="font-semibold text-gray-800 mb-4 flex items-center">
              <span className="mr-2">🗃️</span>
              Tables ({tables.length})
            </h3>
            
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-500"></div>
              </div>
            ) : tables.length === 0 ? (
              <p className="text-gray-500 text-sm">No tables found</p>
            ) : (
              <div className="space-y-2">
                {tables.map((table) => (
                  <button
                    key={table}
                    onClick={() => handleTableSelect(table)}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors duration-200 text-sm ${
                      selectedTable === table
                        ? 'bg-indigo-500 text-white'
                        : 'bg-white/20 text-gray-700 hover:bg-white/30'
                    }`}
                  >
                    📊 {table}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          {!selectedTable ? (
            <div className="glass-card p-8 text-center">
              <div className="text-gray-500 mb-4">
                <span className="text-4xl">📊</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-700 mb-2">Select a Table</h3>
              <p className="text-gray-600">Choose a table from the sidebar to view its data and structure.</p>
            </div>
          ) : (
            <div className="space-y-6">
              {/* Table Info */}
              <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-semibold text-gray-800">
                    📊 {selectedTable}
                  </h3>
                  <div className="flex items-center space-x-4 text-sm text-gray-600">
                    <span>Columns: {tableSchema.length}</span>
                    <span>Records: {tableData.length}</span>
                  </div>
                </div>

                {/* Schema Info */}
                {tableSchema.length > 0 && (
                  <div className="mb-6">
                    <h4 className="font-medium text-gray-700 mb-3">Schema</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {tableSchema.map((column, index) => (
                        <div key={index} className="bg-white/30 rounded-lg p-3">
                          <div className="font-medium text-gray-800 text-sm">{column.name}</div>
                          <div className="text-xs text-gray-600">{column.type}</div>
                          {column.primary_key && (
                            <div className="text-xs text-blue-600 mt-1">🔑 Primary Key</div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Table Data */}
              <div className="glass-card p-6">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="font-medium text-gray-700">Sample Data (First 50 records)</h4>
                  <button
                    onClick={() => fetchTableData(selectedTable)}
                    className="px-3 py-1 bg-indigo-500 text-white rounded text-sm hover:bg-indigo-600 transition-colors duration-200"
                  >
                    🔄 Refresh
                  </button>
                </div>

                {dataLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
                  </div>
                ) : tableData.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No data found in this table
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b border-gray-200">
                          {Object.keys(tableData[0] || {}).map((column) => (
                            <th key={column} className="text-left py-3 px-2 font-medium text-gray-700">
                              <div>{column}</div>
                              <div className="text-xs text-gray-500 font-normal">
                                {getColumnType(column)}
                              </div>
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {tableData.map((row, index) => (
                          <tr key={index} className="border-b border-gray-100 hover:bg-white/20">
                            {Object.values(row).map((value, colIndex) => (
                              <td key={colIndex} className="py-2 px-2 text-gray-800">
                                {formatValue(value)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default DatabaseViewer;