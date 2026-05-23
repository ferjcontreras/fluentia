# Technical Writing Style Guidelines

## Purpose

This document defines the writing style for technical documentation, issue descriptions, commit messages, and other technical content in this project. The goal is to produce clear, honest, and professional engineering documentation.

## Core Principles

### 1. Precision Over Persuasion

Write to inform, not to convince or impress.

**Do:**
- "The embedding client reduces embedding computation time"
- "This implementation uses Elasticsearch for candidate generation"
- "The test suite includes 205 unit tests"

**Don't:**
- "Our cutting-edge embedding client delivers amazing performance"
- "This leverages sophisticated semantic search technology"
- "Comprehensive test coverage ensures bulletproof reliability"

### 2. Direct Language

State facts directly without unnecessary qualifiers or marketing language.

**Do:**
- "This function validates input parameters"
- "The recommender uses a two-stage architecture"
- "Tests run in milliseconds"

**Don't:**
- "This powerful function robustly validates input parameters"
- "The recommender leverages an advanced two-stage architecture"
- "Tests execute with lightning-fast speed"

### 3. Avoid Superlatives and Hype

Remove words that exaggerate or add subjective value judgments.

**Words to avoid:**
- state-of-the-art, cutting-edge, revolutionary, groundbreaking
- sophisticated, advanced, powerful, robust
- amazing, incredible, fantastic, awesome
- best-in-class, industry-leading, world-class
- seamless, effortless, intuitive (unless specifically describing UX)
- comprehensive, complete (unless literally true)
- enterprise-grade, production-ready (unless backed by specific criteria)

**Acceptable alternatives:**
- Instead of "sophisticated algorithm" → "algorithm that handles X, Y, Z cases"
- Instead of "powerful API" → "API that supports async operations"
- Instead of "state-of-the-art solution" → "implementation that uses embeddings and reranking"
- Instead of "comprehensive testing" → "unit, integration, and e2e tests"

### 4. Technical Honesty

Acknowledge limitations, uncertainties, and incomplete work.

**Do:**
- "Integration tests are approximately 80% complete"
- "This approach may not be suitable for X use case"
- "The current implementation does not handle edge case Y"
- "Question: Should we use BM25 or semantic search for this field?"

**Don't:**
- Omit known limitations
- Claim completeness when work is partial
- Present opinions as facts without acknowledging them as such

### 5. Engineering Tone

Write as if communicating with competent engineering colleagues. Assume technical competence but not omniscience.

**Characteristics:**
- Factual and objective
- Professional but not overly formal
- Assumes reader has technical knowledge
- Provides context when introducing project-specific concepts
- Uses standard technical terminology
- Explains "why" when design decisions are not obvious

**Do:**
- "The recommender uses a two-stage architecture because candidate generation must be fast while reranking can be more computationally expensive"
- "Tests are organized into unit/integration/e2e categories to maintain clear boundaries"
- "The Bedrock client supports multiple embedding models to allow experimentation"

**Don't:**
- Explain basic programming concepts (e.g., what a function is)
- Use condescending language
- Over-explain obvious technical choices

### 6. Structure and Clarity

Organize information for scanning and quick comprehension.

**Techniques:**
- Use headers to create clear sections
- Lead with the most important information
- Use bullet points for lists
- Use code blocks for code or configuration examples
- Use tables for comparisons
- Keep paragraphs short (2-4 sentences)
- Use bold for emphasis sparingly

**Example structure:**
```markdown
## Feature Name

Brief description (1-2 sentences).

### Implementation

Technical details about how it works.

### Configuration

How to configure or use it.

### Known Limitations

Current constraints or incomplete aspects.
```

### 7. Active Voice (Usually)

Prefer active voice for clarity, but passive voice is acceptable when appropriate.

**Do:**
- "The script validates input parameters" (active)
- "The embedding client handles concurrent requests" (active)
- "Input parameters are validated before processing" (passive but acceptable)

**Don't:**
- "Input parameters are validated by the script through a validation process" (unnecessarily passive and wordy)

### 8. Concrete Over Abstract

Provide specific details rather than vague descriptions.

**Do:**
- "The configuration supports BM25, semantic, and hybrid search"
- "Candidate generation processes 10,000 documents in under 100ms"
- "The system includes Elasticsearch indexing, embedding generation, and LLM reranking"

**Don't:**
- "The configuration is flexible"
- "Candidate generation is fast"
- "The system includes modern search features"

## Document-Specific Guidelines

### Commit Messages

Follow conventional commits format:

```
<type>: <brief description>

<optional detailed explanation>
```

**Types:** feat, fix, docs, chore, refactor, test, ci

**Do:**
- `feat: Add Cohere v4 embedding model support to Bedrock client`
- `fix: Handle edge case in BM25 scoring for empty fields`
- `docs: Add instance database scripts reference guide`

**Don't:**
- `feat: Add awesome new feature that revolutionizes search`
- `fix: Fix bug` (too vague)

### Issue Descriptions

Structure:
1. **Overview**: What is being discussed or requested (2-3 sentences)
2. **Details**: Technical specifics organized by topic
3. **Open Questions**: Decisions that need team input
4. **Next Steps**: Concrete actions or decisions needed

Use headers, bullet points, and clear sections.

### Documentation (README, guides)

- Start with what the component does, not why it's great
- Provide examples early
- Include both common and edge cases
- Document known limitations
- Keep language factual and descriptive

### Code Comments

- Explain "why", not "what" (code shows what)
- Document non-obvious design decisions
- Acknowledge workarounds or technical debt
- Keep brief and factual

## Examples

### Example 1: Feature Description

**Poor:**
```
Our revolutionary semantic search system leverages cutting-edge embedding
technology to deliver blazing-fast performance and seamless integration with
modern LLM APIs. It's the most sophisticated solution available.
```

**Good:**
```
The recommender uses embeddings to find semantically similar candidates.
This approach handles synonyms and related concepts better than keyword matching.

Example:
- Query: "machine learning engineer"
- Matches: "ML engineer", "data scientist with ML focus", "AI researcher"
```

### Example 2: Issue Discussion

**Poor:**
```
We need to decide on the best possible embedding model for our project.
There are several amazing options available, and we should choose the
most cutting-edge solution that will future-proof our codebase.
```

**Good:**
```
The system currently supports Bedrock embedding models.

Question: Should we add support for OpenAI embeddings or other providers?

Context:
- Bedrock: Already integrated, supports Cohere and Amazon Titan models
- OpenAI: Different API, would require new client implementation
- Cost considerations: Bedrock typically cheaper for our use case

Please share preferences based on model performance and cost requirements.
```

### Example 3: Technical Documentation

**Poor:**
```
Our comprehensive two-stage architecture provides world-class performance
with a sophisticated candidate generation and reranking system that ensures
bulletproof accuracy.
```

**Good:**
```
The recommender uses a two-stage architecture:

- Candidate generation: Fast retrieval of top 100-1000 candidates using Elasticsearch
- Reranking: More expensive scoring of candidates using LLM or specialized models

This structure balances speed and quality. Candidate generation handles the
full corpus efficiently, while reranking applies expensive models to a small set.
```

## When to Deviate

These guidelines apply to technical documentation and communication. They may not apply to:

- Marketing materials (if needed, separate from technical docs)
- User-facing UI text (different brevity/clarity requirements)
- Legal or compliance documentation (different standards)

## Summary

Good technical writing is:
- Precise and factual
- Direct and clear
- Honest about limitations
- Free of marketing language
- Structured for scanning
- Respectful of the reader's technical knowledge

The goal is documentation that helps engineers understand, evaluate, and use the code effectively.
