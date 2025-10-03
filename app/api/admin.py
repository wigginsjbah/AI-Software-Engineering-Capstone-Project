"""
Database Admin API endpoints
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
import sqlite3
import os
from pathlib import Path

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/database-viewer", response_class=HTMLResponse)
async def database_viewer():
    """Web interface to view all databases"""
    
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Database Viewer - Business Intelligence System</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                margin: 0; padding: 20px; background: #f5f7fa; 
            }
            .header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px;
            }
            .database { 
                background: white; border-radius: 10px; margin: 20px 0; 
                padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
            }
            .table { 
                border: 1px solid #e1e8ed; margin: 15px 0; border-radius: 8px; 
                overflow: hidden; 
            }
            .table-header { 
                background: #f8fafc; padding: 15px; font-weight: 600; 
                border-bottom: 1px solid #e1e8ed; 
            }
            .table-content { padding: 15px; }
            table { width: 100%; border-collapse: collapse; }
            th, td { 
                border: 1px solid #e1e8ed; padding: 8px 12px; text-align: left; 
                font-size: 14px;
            }
            th { background-color: #f8fafc; font-weight: 600; }
            .row-count { 
                color: #64748b; font-weight: normal; font-size: 14px; 
                margin-left: 10px;
            }
            .db-stats { 
                display: flex; gap: 20px; margin: 10px 0; 
                flex-wrap: wrap;
            }
            .stat { 
                background: #f1f5f9; padding: 10px 15px; border-radius: 6px; 
                font-size: 14px;
            }
            .loading { text-align: center; padding: 40px; color: #64748b; }
            .error { color: #dc2626; background: #fef2f2; padding: 15px; border-radius: 6px; }
            .company-badge { 
                background: #3b82f6; color: white; padding: 4px 8px; 
                border-radius: 4px; font-size: 12px; margin-left: 10px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🗄️ Database Viewer</h1>
            <p>Comprehensive view of all business databases and company data</p>
        </div>
        
        <div id="loading" class="loading">
            <h3>🔄 Loading database information...</h3>
        </div>
        
        <div id="databases"></div>
        
        <script>
            async function loadDatabases() {
                try {
                    const response = await fetch('/admin/database-data');
                    const data = await response.json();
                    
                    document.getElementById('loading').style.display = 'none';
                    
                    const container = document.getElementById('databases');
                    container.innerHTML = '';
                    
                    if (data.databases.length === 0) {
                        container.innerHTML = '<div class="error">No databases found</div>';
                        return;
                    }
                    
                    data.databases.forEach(db => {
                        const dbDiv = document.createElement('div');
                        dbDiv.className = 'database';
                        
                        let tableCount = db.tables.length;
                        let totalRows = db.tables.reduce((sum, table) => sum + table.row_count, 0);
                        
                        let html = `<h2>📊 ${db.name}`;
                        if (db.name.includes('Company:')) {
                            html += '<span class="company-badge">COMPANY DB</span>';
                        }
                        html += '</h2>';
                        
                        html += `<div class="db-stats">
                                   <div class="stat">📍 <strong>Path:</strong> ${db.path}</div>
                                   <div class="stat">📋 <strong>Tables:</strong> ${tableCount}</div>
                                   <div class="stat">📊 <strong>Total Rows:</strong> ${totalRows}</div>
                                 </div>`;
                        
                        if (db.error) {
                            html += `<div class="error">❌ Error: ${db.error}</div>`;
                        }
                        
                        db.tables.forEach(table => {
                            html += `<div class="table">
                                       <div class="table-header">
                                         📋 <strong>${table.name}</strong>
                                         <span class="row-count">(${table.row_count} rows)</span>
                                       </div>
                                       <div class="table-content">`;
                            
                            if (table.data.length > 0) {
                                html += '<table><thead><tr>';
                                table.columns.forEach(col => {
                                    html += `<th>${col}</th>`;
                                });
                                html += '</tr></thead><tbody>';
                                
                                table.data.forEach(row => {
                                    html += '<tr>';
                                    row.forEach(cell => {
                                        // Truncate long text
                                        let displayCell = cell;
                                        if (typeof cell === 'string' && cell.length > 50) {
                                            displayCell = cell.substring(0, 50) + '...';
                                        }
                                        html += `<td title="${cell}">${displayCell}</td>`;
                                    });
                                    html += '</tr>';
                                });
                                html += '</tbody></table>';
                                
                                if (table.row_count > 10) {
                                    html += `<p style="color: #64748b; font-style: italic; margin-top: 10px;">
                                              Showing first 10 of ${table.row_count} rows</p>`;
                                }
                            } else {
                                html += '<p style="color: #64748b; font-style: italic;">No data</p>';
                            }
                            
                            html += '</div></div>';
                        });
                        
                        dbDiv.innerHTML = html;
                        container.appendChild(dbDiv);
                    });
                } catch (error) {
                    console.error('Error loading databases:', error);
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('databases').innerHTML = 
                        '<div class="error">❌ Error loading database data: ' + error.message + '</div>';
                }
            }
            
            loadDatabases();
        </script>
    </body>
    </html>
    """
    return html_content

@router.get("/database-data")
async def get_database_data():
    """API endpoint to get all database data"""
    
    def get_db_data(db_path, db_name):
        """Extract data from a database"""
        if not os.path.exists(db_path):
            return None
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            db_data = {
                "name": db_name,
                "path": db_path,
                "tables": []
            }
            
            for table in tables:
                table_name = table[0]
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name});")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                
                # Get sample data (first 10 rows)
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 10;")
                rows = cursor.fetchall()
                
                db_data["tables"].append({
                    "name": table_name,
                    "columns": columns,
                    "row_count": count,
                    "data": rows
                })
            
            conn.close()
            return db_data
            
        except Exception as e:
            return {
                "name": db_name,
                "path": db_path,
                "error": str(e),
                "tables": []
            }
    
    # Find all databases
    databases = []
    base_path = Path(".")
    
    # Main business database
    main_db = "business_data.db"
    if os.path.exists(main_db):
        db_data = get_db_data(main_db, "Main Business Database")
        if db_data:
            databases.append(db_data)
    
    # Company-specific databases
    companies_path = base_path / "companies"
    if companies_path.exists():
        for company_dir in companies_path.iterdir():
            if company_dir.is_dir():
                for db_file in company_dir.glob("*.db"):
                    # Try to get company name from metadata
                    company_name = company_dir.name
                    try:
                        conn = sqlite3.connect(str(db_file))
                        cursor = conn.cursor()
                        cursor.execute("SELECT value FROM _company_metadata WHERE key = 'company_name'")
                        result = cursor.fetchone()
                        if result:
                            company_name = result[0]
                        conn.close()
                    except:
                        pass
                    
                    db_data = get_db_data(str(db_file), f"Company: {company_name}")
                    if db_data:
                        databases.append(db_data)
    
    return {"databases": databases}