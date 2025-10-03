# Architecture Decision Record 002: SQLite Database Architecture

**Status:** Accepted  
**Date:** 2025-10-03  
**Deciders:** Engineering Team  

## Context

Our Business Intelligence RAG Chatbot needs to support multiple business types (retail, healthcare, finance) with different data schemas. We need a database solution that can:
- Handle different business domain schemas dynamically
- Support AI-generated sample data
- Provide fast query performance for real-time chat
- Enable easy deployment and local development
- Support company-specific data isolation

## Decision

We will use **SQLite databases with business-specific schemas** where each company gets its own database file.

## Rationale

### Pros:
- **Zero Configuration:** No database server setup required
- **File-based Isolation:** Each company database is completely isolated
- **Portability:** Database files can be easily backed up and moved
- **ACID Compliance:** Full transaction support for data integrity
- **Performance:** Excellent read performance for analytical queries
- **Embedded:** No external dependencies or services required
- **Cross-platform:** Works consistently across development environments

### Cons:
- **Concurrent Writes:** Limited concurrent write performance
- **Scalability:** Not suitable for very large datasets (>100GB)
- **Network Access:** Cannot be accessed directly over network
- **Advanced Features:** Limited compared to PostgreSQL/MySQL

### Alternatives Considered:

1. **PostgreSQL**
   - Pros: Advanced features, excellent concurrency, JSON support
   - Cons: Requires server setup, more complex deployment, overkill for our scale

2. **MySQL**
   - Pros: Mature, good performance, widespread adoption
   - Cons: Server dependency, licensing considerations, complex setup

3. **MongoDB**
   - Pros: Schema flexibility, JSON-native, good scaling
   - Cons: NoSQL limitations for analytical queries, less mature ecosystem

4. **Single Database with Multi-tenancy**
   - Pros: Easier management, shared resources
   - Cons: Data isolation risks, complex schema management, security concerns

## Architecture Details

### Database Structure:
```
project_root/
├── armandos_aquarium_database.db    # Example company database
├── company_name_database.db         # Auto-generated company databases
└── app/
    └── api/
        └── enhanced_companies.py    # Schema definitions
```

### Schema Strategy:
- **Business Type Schemas:** Retail, Healthcare, Finance
- **Dynamic Schema Selection:** Based on company business type
- **Common Tables:** All schemas include customers, products, orders
- **Specialized Tables:** Business-specific tables (e.g., patients for healthcare)

### Business Schemas:

#### Retail Schema:
- customers, products, orders, order_items, reviews, inventory

#### Healthcare Schema:
- customers (patients), products (treatments), orders (appointments)
- medical_records, insurance_info, healthcare_providers

#### Finance Schema:
- customers (clients), financial_products, accounts, transactions
- loans, portfolio_holdings

## Consequences

### Positive:
- **Simple Deployment:** No database server management
- **Perfect Isolation:** Complete data separation between companies
- **Fast Development:** Immediate local development setup
- **Easy Backup:** Simple file-based backup strategy
- **Predictable Performance:** Consistent query performance

### Negative:
- **Scaling Limitations:** May need migration for very large datasets
- **Concurrent Access:** Limited concurrent write operations
- **Advanced Analytics:** Limited compared to full RDBMS features
- **Replication:** No built-in replication for high availability

### Neutral:
- **SQL Compatibility:** Standard SQL queries work as expected
- **Tool Support:** Works with standard database tools and ORMs

## Implementation Guidelines

### Database Creation:
```python
# Each company gets isolated database
db_path = f"{clean_company_name}_database.db"
engine = create_engine(f"sqlite:///{db_path}")
```

### Schema Management:
- Business type determines table structure
- Dynamic schema creation based on company profile
- Consistent naming conventions across business types

### Query Optimization:
- Create indexes on frequently queried columns
- Use EXPLAIN QUERY PLAN for performance analysis
- Implement connection pooling for concurrent access

### Data Integrity:
- Foreign key constraints enabled
- Transaction isolation for data consistency
- Regular database integrity checks

## Migration Strategy

### If Scaling Becomes Necessary:
1. **PostgreSQL Migration:** Can migrate SQLite → PostgreSQL
2. **Partitioning:** Separate databases by company already provides natural partitioning
3. **Sharding:** Current architecture naturally supports horizontal sharding

### Data Export:
- Standard SQL dump capabilities
- JSON export for API integrations
- CSV export for analysis tools

## Related Decisions

- ADR-001: FastAPI Framework Selection
- ADR-003: AI Integration Strategy
- ADR-005: Multi-Company Data Architecture

## Security Considerations

- File-level permissions for database access control
- Company data completely isolated at database level
- No cross-company data leakage possible
- Regular security audits of database access patterns

---
*This ADR follows the format described in Michael Nygard's article on Architecture Decision Records.*