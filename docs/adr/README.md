# Architecture Decision Record Index

This directory contains Architecture Decision Records (ADRs) for the Business Intelligence RAG Chatbot project. ADRs document the key architectural decisions made during development, providing context, rationale, and consequences for future reference.

## What are ADRs?

Architecture Decision Records are lightweight documents that capture important architectural decisions made during a project, along with their context and consequences. They help teams understand why certain technical choices were made and provide guidance for future decisions.

## ADR Format

Each ADR follows a consistent format:
- **Status**: Current status (Proposed, Accepted, Deprecated, Superseded)
- **Date**: When the decision was made
- **Context**: The situation that requires a decision
- **Decision**: The chosen solution
- **Rationale**: Why this solution was chosen (pros, cons, alternatives)
- **Consequences**: Expected outcomes and implications

## Current ADRs

### [ADR-001: FastAPI Framework Selection](001-fastapi-framework-selection.md)
**Status**: Accepted  
**Decision**: Use FastAPI as the backend web framework  
**Key Rationale**: Modern async support, automatic API documentation, type safety, and excellent performance for AI API integrations.

### [ADR-002: SQLite Database Architecture](002-sqlite-database-architecture.md)
**Status**: Accepted  
**Decision**: Use SQLite databases with business-specific schemas and company isolation  
**Key Rationale**: Zero configuration, file-based isolation, portability, and excellent read performance for analytical queries.

### [ADR-003: OpenAI and Multi-Agent RAG Architecture](003-openai-multi-agent-rag-architecture.md)
**Status**: Accepted  
**Decision**: Implement multi-agent RAG using OpenAI GPT models with ChromaDB vector storage  
**Key Rationale**: State-of-the-art NLP capabilities, specialized agent architecture, and comprehensive data source integration.

### [ADR-004: Glassmorphism Frontend with Vanilla JavaScript](004-glassmorphism-frontend-vanilla-js.md)
**Status**: Accepted  
**Decision**: Build frontend using glassmorphism design with vanilla HTML/CSS/JavaScript  
**Key Rationale**: Zero dependencies, fast performance, simple deployment, and modern aesthetic appeal.

## Decision Dependencies

```
ADR-001 (FastAPI)
    ↓
ADR-002 (SQLite) ← → ADR-003 (OpenAI/RAG)
    ↓                      ↓
ADR-004 (Frontend) ← ← ← ← ←
```

## Guidelines for New ADRs

### When to Create an ADR:
- Significant architectural or technology choices
- Design patterns that affect multiple components
- Third-party service integrations
- Performance or security trade-offs
- Changes that impact team workflow

### ADR Naming Convention:
`XXX-descriptive-title.md` where XXX is a zero-padded sequential number.

### Status Transitions:
- **Proposed** → **Accepted**: Decision approved and implemented
- **Accepted** → **Deprecated**: Decision no longer recommended for new work
- **Accepted** → **Superseded**: Replaced by a newer decision (reference the new ADR)

## Related Documentation

- [Product Requirements Document (PRD)](../PRD.md)
- [Technical Architecture Overview](../architecture.md) *(to be created)*
- [API Documentation](../../README.md#api-endpoints)

## ADR Template

Use this template for new ADRs:

```markdown
# Architecture Decision Record XXX: [Title]

**Status:** [Proposed | Accepted | Deprecated | Superseded]  
**Date:** YYYY-MM-DD  
**Deciders:** [List of people involved in the decision]  

## Context
[Describe the situation that requires a decision]

## Decision
[State the decision that was made]

## Rationale
### Pros:
- [List advantages of the chosen solution]

### Cons:
- [List disadvantages of the chosen solution]

### Alternatives Considered:
1. **[Alternative 1]**
   - Pros: [advantages]
   - Cons: [disadvantages]

## Consequences
### Positive:
- [Expected benefits]

### Negative:
- [Expected costs or risks]

### Neutral:
- [Other impacts]

## Related Decisions
- [Links to related ADRs]

---
*This ADR follows the format described in Michael Nygard's article on Architecture Decision Records.*
```

## References

- [Michael Nygard's ADR article](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions)
- [ADR GitHub organization](https://adr.github.io/)
- [ThoughtWorks Technology Radar on ADRs](https://www.thoughtworks.com/radar/techniques/lightweight-architecture-decision-records)