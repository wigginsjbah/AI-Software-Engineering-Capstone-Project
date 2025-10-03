#!/usr/bin/env python3
"""
Simple Context Builder for SQL Databases

This context builder understands SQL table relationships and provides
clear, structured context to the RAG system about business data.
"""

import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

class SimpleContextBuilder:
    """
    A simple context builder that understands SQL relationships
    and provides clear business context to the RAG system.
    """
    
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.schema_info = None
        self.table_relationships = None
        self._analyze_database()
    
    def _analyze_database(self):
        """Analyze the database schema and relationships"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name != '_company_metadata'")
            tables = [row[0] for row in cursor.fetchall()]
            
            self.schema_info = {}
            self.table_relationships = {}
            
            for table in tables:
                # Get table info
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                
                # Get foreign keys
                cursor.execute(f"PRAGMA foreign_key_list({table})")
                foreign_keys = cursor.fetchall()
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                self.schema_info[table] = {
                    "columns": [{"name": col[1], "type": col[2], "nullable": not col[3], "pk": bool(col[5])} for col in columns],
                    "foreign_keys": [{"column": fk[3], "references_table": fk[2], "references_column": fk[4]} for fk in foreign_keys],
                    "row_count": row_count
                }
                
                # Build relationship map
                self.table_relationships[table] = {
                    "references": [fk["references_table"] for fk in self.schema_info[table]["foreign_keys"]],
                    "referenced_by": []
                }
            
            # Complete the relationship map
            for table, info in self.schema_info.items():
                for fk in info["foreign_keys"]:
                    ref_table = fk["references_table"]
                    if ref_table in self.table_relationships:
                        self.table_relationships[ref_table]["referenced_by"].append(table)
            
            conn.close()
            
        except Exception as e:
            print(f"Error analyzing database: {e}")
            self.schema_info = {}
            self.table_relationships = {}
    
    def get_business_summary(self) -> str:
        """Get a high-level summary of the business data"""
        if not self.schema_info:
            return "No business data available."
        
        summary_parts = []
        
        # Determine business type from tables
        table_names = set(self.schema_info.keys())
        
        if "products" in table_names and "orders" in table_names:
            business_type = "retail/e-commerce"
            summary_parts.append(f"This is a {business_type} business with:")
            
            if "categories" in table_names:
                cat_count = self.schema_info["categories"]["row_count"]
                summary_parts.append(f"• {cat_count} product categories")
            
            prod_count = self.schema_info["products"]["row_count"]
            summary_parts.append(f"• {prod_count} products in inventory")
            
            if "customers" in table_names:
                cust_count = self.schema_info["customers"]["row_count"]
                summary_parts.append(f"• {cust_count} customers")
            
            order_count = self.schema_info["orders"]["row_count"]
            summary_parts.append(f"• {order_count} orders processed")
            
            if "order_items" in table_names:
                item_count = self.schema_info["order_items"]["row_count"]
                summary_parts.append(f"• {item_count} order line items")
        
        elif "patients" in table_names and "appointments" in table_names:
            business_type = "healthcare practice"
            summary_parts.append(f"This is a {business_type} with:")
            
            if "specialties" in table_names:
                spec_count = self.schema_info["specialties"]["row_count"]
                summary_parts.append(f"• {spec_count} medical specialties")
            
            if "doctors" in table_names:
                doc_count = self.schema_info["doctors"]["row_count"]
                summary_parts.append(f"• {doc_count} doctors")
            
            patient_count = self.schema_info["patients"]["row_count"]
            summary_parts.append(f"• {patient_count} patients")
            
            appt_count = self.schema_info["appointments"]["row_count"]
            summary_parts.append(f"• {appt_count} appointments scheduled")
            
            if "treatments" in table_names:
                treat_count = self.schema_info["treatments"]["row_count"]
                summary_parts.append(f"• {treat_count} treatments provided")
        
        elif "users" in table_names and "subscriptions" in table_names:
            business_type = "technology/SaaS company"
            summary_parts.append(f"This is a {business_type} with:")
            
            user_count = self.schema_info["users"]["row_count"]
            summary_parts.append(f"• {user_count} users")
            
            if "products" in table_names:
                prod_count = self.schema_info["products"]["row_count"]
                summary_parts.append(f"• {prod_count} software products")
            
            sub_count = self.schema_info["subscriptions"]["row_count"]
            summary_parts.append(f"• {sub_count} subscriptions")
            
            if "usage_logs" in table_names:
                log_count = self.schema_info["usage_logs"]["row_count"]
                summary_parts.append(f"• {log_count} usage events logged")
        
        else:
            summary_parts.append("This business has the following data:")
            for table, info in self.schema_info.items():
                count = info["row_count"]
                summary_parts.append(f"• {table}: {count} records")
        
        return "\\n".join(summary_parts)
    
    def get_table_context(self, query: str) -> str:
        """Get relevant table context based on a query"""
        if not self.schema_info:
            return "No database schema available."
        
        # Simple keyword matching to find relevant tables
        query_lower = query.lower()
        relevant_tables = []
        
        # Define table keywords
        table_keywords = {
            "products": ["product", "item", "inventory", "stock", "catalog", "goods"],
            "categories": ["category", "type", "kind", "classification"],
            "customers": ["customer", "client", "buyer", "user"],
            "orders": ["order", "purchase", "sale", "transaction"],
            "order_items": ["item", "line item", "order detail"],
            "patients": ["patient", "medical record"],
            "doctors": ["doctor", "physician", "provider"],
            "appointments": ["appointment", "visit", "schedule"],
            "treatments": ["treatment", "procedure", "service"],
            "specialties": ["specialty", "department", "medical field"],
            "users": ["user", "account", "member"],
            "subscriptions": ["subscription", "plan", "membership"],
            "usage_logs": ["usage", "activity", "log", "analytics"],
            "product_categories": ["category", "type", "kind"]
        }
        
        # Find relevant tables
        for table, keywords in table_keywords.items():
            if table in self.schema_info:
                if any(keyword in query_lower for keyword in keywords):
                    relevant_tables.append(table)
        
        # If no specific matches, include key business tables
        if not relevant_tables:
            key_tables = ["products", "customers", "orders", "patients", "users", "appointments"]
            relevant_tables = [table for table in key_tables if table in self.schema_info]
        
        # Build context
        context_parts = []
        
        for table in relevant_tables[:3]:  # Limit to 3 most relevant tables
            info = self.schema_info[table]
            context_parts.append(f"\\n**{table.upper()} Table:**")
            context_parts.append(f"Records: {info['row_count']}")
            
            # Key columns
            key_columns = []
            for col in info["columns"]:
                if col["pk"] or "id" in col["name"].lower():
                    key_columns.append(f"{col['name']} ({col['type']})")
                elif any(word in col["name"].lower() for word in ["name", "title", "description", "email", "phone"]):
                    key_columns.append(f"{col['name']} ({col['type']})")
            
            if key_columns:
                context_parts.append(f"Key columns: {', '.join(key_columns[:5])}")
            
            # Relationships
            relationships = self.table_relationships.get(table, {})
            if relationships["references"]:
                context_parts.append(f"References: {', '.join(relationships['references'])}")
            if relationships["referenced_by"]:
                context_parts.append(f"Referenced by: {', '.join(relationships['referenced_by'])}")
        
        return "\\n".join(context_parts)
    
    def get_business_metrics(self) -> Dict[str, Any]:
        """Get key business metrics from the database"""
        metrics = {}
        
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Revenue metrics (if applicable)
            if "orders" in self.schema_info and "total_amount" in [col["name"] for col in self.schema_info["orders"]["columns"]]:
                cursor.execute("SELECT SUM(total_amount), AVG(total_amount), COUNT(*) FROM orders")
                total_revenue, avg_order, order_count = cursor.fetchone()
                metrics["revenue"] = {
                    "total_revenue": total_revenue or 0,
                    "average_order_value": avg_order or 0,
                    "total_orders": order_count
                }
            
            # Customer metrics
            if "customers" in self.schema_info:
                cursor.execute("SELECT COUNT(*) FROM customers")
                customer_count = cursor.fetchone()[0]
                metrics["customers"] = {"total_customers": customer_count}
            
            # Product metrics
            if "products" in self.schema_info:
                cursor.execute("SELECT COUNT(*) FROM products")
                product_count = cursor.fetchone()[0]
                metrics["products"] = {"total_products": product_count}
                
                # Stock levels if available
                if "stock_quantity" in [col["name"] for col in self.schema_info["products"]["columns"]]:
                    cursor.execute("SELECT SUM(stock_quantity), AVG(stock_quantity) FROM products")
                    total_stock, avg_stock = cursor.fetchone()
                    metrics["products"]["total_stock"] = total_stock or 0
                    metrics["products"]["average_stock"] = avg_stock or 0
            
            # Healthcare metrics
            if "patients" in self.schema_info:
                cursor.execute("SELECT COUNT(*) FROM patients")
                patient_count = cursor.fetchone()[0]
                metrics["healthcare"] = {"total_patients": patient_count}
                
                if "appointments" in self.schema_info:
                    cursor.execute("SELECT COUNT(*) FROM appointments")
                    appt_count = cursor.fetchone()[0]
                    metrics["healthcare"]["total_appointments"] = appt_count
            
            # Technology metrics
            if "users" in self.schema_info:
                cursor.execute("SELECT COUNT(*) FROM users")
                user_count = cursor.fetchone()[0]
                metrics["technology"] = {"total_users": user_count}
                
                if "subscriptions" in self.schema_info:
                    cursor.execute("SELECT COUNT(*) FROM subscriptions WHERE status = 'active'")
                    active_subs = cursor.fetchone()[0]
                    metrics["technology"]["active_subscriptions"] = active_subs
            
            conn.close()
            
        except Exception as e:
            print(f"Error calculating metrics: {e}")
        
        return metrics
    
    def get_sample_data(self, table: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample data from a specific table"""
        if table not in self.schema_info:
            return []
        
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get column names
            columns = [col["name"] for col in self.schema_info[table]["columns"]]
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {table} LIMIT {limit}")
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            sample_data = []
            for row in rows:
                sample_data.append(dict(zip(columns, row)))
            
            conn.close()
            return sample_data
            
        except Exception as e:
            print(f"Error getting sample data: {e}")
            return []
    
    def build_context_for_query(self, query: str) -> str:
        """Build comprehensive context for a specific query"""
        context_parts = []
        
        # Business summary
        context_parts.append("=== BUSINESS OVERVIEW ===")
        context_parts.append(self.get_business_summary())
        
        # Relevant table context
        context_parts.append("\\n=== RELEVANT DATA TABLES ===")
        context_parts.append(self.get_table_context(query))
        
        # Key metrics
        metrics = self.get_business_metrics()
        if metrics:
            context_parts.append("\\n=== KEY BUSINESS METRICS ===")
            for category, metric_data in metrics.items():
                context_parts.append(f"**{category.title()}:**")
                for metric, value in metric_data.items():
                    if isinstance(value, float):
                        context_parts.append(f"  • {metric.replace('_', ' ').title()}: ${value:,.2f}")
                    else:
                        context_parts.append(f"  • {metric.replace('_', ' ').title()}: {value:,}")
        
        return "\\n".join(context_parts)


def main():
    """Test the simple context builder"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python simple_context_builder.py <database_path>")
        return
    
    db_path = sys.argv[1]
    builder = SimpleContextBuilder(db_path)
    
    print("=== DATABASE ANALYSIS ===")
    print(builder.get_business_summary())
    
    print("\\n=== SAMPLE QUERY CONTEXT ===")
    test_query = "What are our top selling products?"
    print(f"Query: {test_query}")
    print(builder.build_context_for_query(test_query))

if __name__ == "__main__":
    main()