# Prompt Vault - NoSQL Backend Evaluation Report

**Issue:** #199  
**Status:** Research Complete  
**Date:** November 5, 2025  
**Research Duration:** 1 Week (Estimated)

---

## Executive Summary

This research evaluates NoSQL backend alternatives for Prompt Vault's content management and search capabilities, comparing them against the current **Supabase (PostgreSQL)** implementation. After comprehensive analysis of cost, search capabilities, data model fit, and integration complexity, **the recommendation is to retain Supabase** with strategic enhancements rather than migrating to a NoSQL solution.

**Recommendation:** **Option A - Retain Supabase** with the following enhancements:
1. Implement `pg_vector` extension for semantic search capabilities
2. Optimize full-text search with PostgreSQL's native `tsvector` and `tsquery`
3. Consider hybrid approach: Supabase for structured data + Firestore for large document storage (if needed)

---

## Current Implementation Analysis

### Current Stack: Supabase (PostgreSQL)

**Current Schema:**
- `prompts` table with structured fields (id, user_id, title, content, description, category, tags, is_public, timestamps)
- Row Level Security (RLS) policies for multi-tenancy
- PostgreSQL arrays for tags
- Automatic timestamp triggers

**Current Capabilities:**
- ✅ Authentication (Google OAuth via Supabase Auth)
- ✅ Row Level Security for data isolation
- ✅ Full-text search via PostgreSQL `LIKE`/`ILIKE` (basic)
- ✅ Structured querying and relationships
- ✅ Transaction support
- ✅ ACID compliance

**Current Limitations:**
- ⚠️ Basic full-text search (no semantic search without extensions)
- ⚠️ No native vector search capabilities (requires `pg_vector` extension)
- ⚠️ May not be optimal for very large unstructured documents

---

## Candidate Backend Evaluation

### Candidate 1: MongoDB Atlas

**Overview:**
MongoDB Atlas is a fully-managed NoSQL database service with strong document storage capabilities.

#### Cost Analysis

**Free Tier (M0):**
- 512MB storage
- Shared RAM (shared with other free tier users)
- No backup
- Limited to 500 connections

**Paid Tiers (Starter):**
- M2: $9/month - 2GB storage, 2GB RAM
- M5: $57/month - 10GB storage, 4GB RAM
- M10: $120/month - 20GB storage, 10GB RAM

**Cost at Scale (estimated for 100K prompts):**
- Storage: ~10GB (assuming 100KB per prompt with metadata)
- Estimated monthly cost: $57-120/month (M5-M10 cluster)
- Additional costs for Atlas Search: $0.10 per 1,000 search operations

#### Search Capabilities

**Atlas Search:**
- ✅ Full-text search with relevance scoring
- ✅ Faceted search (categories, tags)
- ✅ Autocomplete support
- ✅ Vector search available (Atlas Vector Search)
- ✅ Multi-field search with weighted scoring
- ⚠️ Additional cost: $0.10 per 1,000 search operations

**Implementation Complexity:**
- Moderate - requires Atlas Search index configuration
- Vector search requires embedding generation (external service or MongoDB Atlas Functions)

#### Data Model Fit

**Strengths:**
- ✅ Native JSON/Document storage - perfect for structured prompts
- ✅ Flexible schema - can store complex nested structures from FR#240
- ✅ Array support for tags
- ✅ Embedded documents for function definitions

**Example Schema:**
```json
{
  "_id": "uuid",
  "user_id": "uuid",
  "title": "string",
  "content": "string",
  "description": "string",
  "category": "string",
  "tags": ["tag1", "tag2"],
  "is_public": false,
  "metadata": {
    "functions": [...],
    "schema": {...}
  },
  "created_at": "ISODate",
  "updated_at": "ISODate"
}
```

#### Integration Effort

**Estimated Effort:** Medium (2-3 weeks)
- ✅ Official MongoDB Node.js driver available
- ✅ Mongoose ODM for easier schema management
- ⚠️ Need to migrate authentication logic (Supabase Auth → custom or keep Supabase)
- ⚠️ Need to implement RLS equivalent (application-level or MongoDB Realm)
- ⚠️ Need to migrate existing data

**Code Changes Required:**
- Replace Supabase client with MongoDB client
- Rewrite all database queries
- Implement custom authentication or keep Supabase Auth separately
- Migrate RLS policies to application-level security

---

### Candidate 2: Firestore (GCP)

**Overview:**
Firestore is Google Cloud's NoSQL document database, already available in the GCP infrastructure.

#### Cost Analysis

**Free Tier:**
- 1GB storage
- 50K reads/day
- 20K writes/day
- 20K deletes/day

**Paid Tier (Blaze Plan - Pay as you go):**
- Storage: $0.18/GB/month
- Document reads: $0.06 per 100K reads
- Document writes: $0.18 per 100K writes
- Document deletes: $0.02 per 100K deletes

**Cost at Scale (estimated for 100K prompts):**
- Storage: ~10GB = $1.80/month
- Reads: 100K reads/day = 3M/month = $1.80/month
- Writes: 10K writes/day = 300K/month = $0.54/month
- **Total estimated: ~$4-5/month** (very cost-effective)

#### Search Capabilities

**Native Capabilities:**
- ⚠️ **Limited full-text search** - No native full-text search
- ⚠️ **No semantic/vector search** - Would require external vector database
- ✅ Field-based queries with filters
- ✅ Indexed queries for fast lookups
- ⚠️ String matching requires application-level filtering

**Workarounds:**
- Use Algolia/Flexsearch for full-text search (additional cost)
- Use Vertex AI Vector Search (GCP) for semantic search (additional cost)
- Implement client-side search for small datasets

**Implementation Complexity:**
- High - Firestore lacks native full-text search
- Requires external service integration for search capabilities

#### Data Model Fit

**Strengths:**
- ✅ Native document/JSON storage
- ✅ Flexible schema
- ✅ Subcollections for nested data
- ✅ Array support for tags

**Example Schema:**
```javascript
/prompts/{promptId}
{
  userId: "uuid",
  title: "string",
  content: "string",
  description: "string",
  category: "string",
  tags: ["tag1", "tag2"],
  isPublic: false,
  metadata: {
    functions: [...],
    schema: {...}
  },
  createdAt: Timestamp,
  updatedAt: Timestamp
}
```

#### Integration Effort

**Estimated Effort:** Medium-High (2-4 weeks)
- ✅ Firebase Admin SDK available for Node.js
- ✅ Already in GCP infrastructure (no additional provider)
- ⚠️ Need to migrate authentication (or keep Supabase Auth)
- ⚠️ Need to implement RLS equivalent (Firestore Security Rules)
- ⚠️ Need to add external search service (Algolia/Vertex AI)
- ⚠️ Need to migrate existing data

**Code Changes Required:**
- Replace Supabase client with Firestore client
- Rewrite all database queries
- Implement Firestore Security Rules for RLS
- Integrate external search service
- Handle authentication separately

---

### Candidate 3: Re-evaluation of Firestore for Content Management

**Focus:** Use Firestore as a complementary storage layer for large content documents while keeping Supabase for authentication and metadata.

#### Hybrid Architecture Approach

**Option 3A: Supabase + Firestore Hybrid**
- **Supabase (PostgreSQL):** User authentication, metadata, relationships, search indexes
- **Firestore:** Large prompt content documents, version history

**Pros:**
- ✅ Leverage existing GCP infrastructure
- ✅ Keep Supabase Auth (no migration needed)
- ✅ Use Firestore for document storage (cost-effective)
- ✅ Use Supabase for search and relationships

**Cons:**
- ⚠️ Increased complexity (two database systems)
- ⚠️ Data synchronization challenges
- ⚠️ Still need external search service for semantic search

**Cost:**
- Supabase: Current cost (likely free tier or low cost)
- Firestore: ~$4-5/month for document storage
- **Total: Low incremental cost**

---

## Detailed Comparison Matrix

| Criteria | Supabase (Current) | MongoDB Atlas | Firestore | Hybrid (Supabase + Firestore) |
|----------|-------------------|---------------|-----------|-------------------------------|
| **Cost (100K prompts)** | Free tier or ~$25/mo | $57-120/mo | $4-5/mo | $4-5/mo + current Supabase |
| **Full-Text Search** | ✅ Native (with optimization) | ✅ Atlas Search ($0.10/1K ops) | ❌ Requires external | ⚠️ Via Supabase |
| **Semantic/Vector Search** | ✅ pg_vector extension | ✅ Atlas Vector Search | ❌ Requires Vertex AI | ⚠️ Via Supabase pg_vector |
| **Data Model Fit** | ✅ Good (structured) | ✅✅ Excellent (native JSON) | ✅✅ Excellent (native JSON) | ✅✅ Excellent |
| **Authentication** | ✅✅ Built-in (Supabase Auth) | ⚠️ External (custom/Supabase) | ⚠️ External (custom/Supabase) | ✅ Built-in (Supabase Auth) |
| **RLS/Security** | ✅✅ Native RLS policies | ⚠️ Application-level | ⚠️ Security Rules | ✅ Native RLS (Supabase) |
| **Integration Effort** | ✅✅ Already integrated | ⚠️ 2-3 weeks | ⚠️ 2-4 weeks | ⚠️ 1-2 weeks |
| **Migration Complexity** | ✅✅ None (current) | ⚠️ High (full migration) | ⚠️ High (full migration) | ⚠️ Medium (partial) |
| **Scalability** | ✅ Good (up to limits) | ✅✅ Excellent | ✅✅ Excellent | ✅✅ Excellent |
| **Transaction Support** | ✅✅ ACID transactions | ⚠️ Limited | ❌ No transactions | ⚠️ Limited |

---

## Search Capabilities Deep Dive

### Supabase (PostgreSQL) - Enhanced Approach

**Current State:** Basic `LIKE`/`ILIKE` queries

**Enhancement Options:**

1. **Native Full-Text Search (tsvector/tsquery)**
   - ✅ Built into PostgreSQL (no additional cost)
   - ✅ Relevance ranking
   - ✅ Multi-language support
   - ✅ Phrase search
   - **Implementation:** Add `tsvector` column, create GIN index
   - **Cost:** $0 (native feature)

2. **pg_vector Extension (Semantic Search)**
   - ✅ Vector similarity search
   - ✅ Embedding storage and search
   - ✅ Integration with OpenAI/Cohere embeddings
   - **Implementation:** Enable extension, add vector column
   - **Cost:** $0 (open-source extension)
   - **Additional:** Embedding generation cost (OpenAI ~$0.0001 per prompt)

**Example Implementation:**
```sql
-- Full-text search
ALTER TABLE prompts ADD COLUMN search_vector tsvector;
CREATE INDEX prompts_search_idx ON prompts USING GIN(search_vector);

-- Vector search (semantic)
ALTER TABLE prompts ADD COLUMN embedding vector(1536);
CREATE INDEX prompts_embedding_idx ON prompts USING ivfflat (embedding vector_cosine_ops);
```

### MongoDB Atlas Search

**Capabilities:**
- ✅ Full-text search with relevance scoring
- ✅ Faceted search
- ✅ Autocomplete
- ✅ Vector search (Atlas Vector Search)
- **Cost:** $0.10 per 1,000 search operations
- **At 10K searches/day:** ~$30/month additional cost

### Firestore Search

**Capabilities:**
- ❌ No native full-text search
- ⚠️ Requires Algolia ($0.50 per 1,000 searches) or Flexsearch (self-hosted)
- ⚠️ Vector search requires Vertex AI Vector Search (additional cost)
- **At 10K searches/day:** ~$150/month (Algolia) or infrastructure cost (self-hosted)

---

## Cost Projection Analysis

### Scenario: 100K Prompts, 10K Daily Searches

| Solution | Monthly Storage | Monthly Search | Monthly Auth | Total Monthly |
|----------|----------------|----------------|--------------|---------------|
| **Supabase (Current)** | $0-25 | $0 | $0 | **$0-25** |
| **Supabase + pg_vector** | $0-25 | $0 | $0 | **$0-25** |
| **MongoDB Atlas M5** | $57 | $30 | $0 | **$87** |
| **Firestore** | $1.80 | $150 (Algolia) | $0 | **$152** |
| **Hybrid (Supabase + Firestore)** | $1.80 | $0 | $0 | **$1.80 + Supabase** |

**Key Insight:** Supabase with native enhancements is the most cost-effective solution, especially with free tier or low-cost hosting.

---

## Recommendation: Option A - Retain Supabase

### Justification

1. **Cost Efficiency:** 
   - Supabase free tier or low-cost hosting ($0-25/month)
   - No additional search service costs with native PostgreSQL features
   - MongoDB Atlas would cost 3-6x more

2. **Search Capabilities:**
   - PostgreSQL's native `tsvector`/`tsquery` provides excellent full-text search
   - `pg_vector` extension enables semantic search without external services
   - Performance is excellent for the expected scale (100K-1M prompts)

3. **Migration Cost:**
   - High cost to migrate authentication, data, and application code
   - Estimated 2-4 weeks of development time
   - Risk of introducing bugs and breaking existing functionality

4. **Current Architecture:**
   - Supabase Auth is already working perfectly
   - RLS policies are implemented and tested
   - Application code is functional and tested

5. **Future Scalability:**
   - PostgreSQL scales well up to millions of records
   - Can always migrate later if needed (no lock-in at current stage)
   - Supabase offers horizontal scaling options

### Recommended Enhancements

**Phase 1: Optimize Full-Text Search (1-2 days)**
```sql
-- Add full-text search column
ALTER TABLE prompts 
ADD COLUMN search_vector tsvector 
GENERATED ALWAYS AS (
  to_tsvector('english', 
    coalesce(title, '') || ' ' || 
    coalesce(content, '') || ' ' || 
    coalesce(description, '')
  )
) STORED;

-- Create index
CREATE INDEX prompts_search_vector_idx 
ON prompts USING GIN(search_vector);

-- Update queries to use full-text search
-- Example: SELECT * FROM prompts WHERE search_vector @@ to_tsquery('english', 'search term');
```

**Phase 2: Add Semantic Search (1 week)**
```sql
-- Enable pg_vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Add embedding column
ALTER TABLE prompts ADD COLUMN embedding vector(1536);

-- Create vector index
CREATE INDEX prompts_embedding_idx 
ON prompts USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Add function to generate embeddings (via Supabase Edge Function or external service)
```

**Phase 3: Hybrid Storage (Optional, if needed)**
- If prompt content becomes very large (>100KB per prompt)
- Consider storing large content in Firestore
- Keep metadata and search indexes in Supabase
- This is a future optimization, not needed now

---

## Alternative: Option B - Hybrid Approach (If Needed Later)

**When to Consider:**
- Prompt content exceeds 100KB per prompt on average
- Need to store large binary files (images, PDFs) with prompts
- Need version history for large documents

**Implementation:**
- Keep Supabase for: Authentication, metadata, search indexes, relationships
- Use Firestore for: Large prompt content, version history, binary files
- Cost: ~$4-5/month for Firestore + current Supabase cost

**Migration Effort:** Medium (1-2 weeks)
- Move large content to Firestore
- Keep references in Supabase
- Update application code to fetch from both

---

## Conclusion

**Final Recommendation: Retain Supabase with Strategic Enhancements**

The research clearly shows that:
1. **Supabase is cost-effective** - Free tier or low-cost hosting with no additional search service fees
2. **Search capabilities are sufficient** - Native PostgreSQL full-text search + pg_vector for semantic search
3. **Migration cost is high** - 2-4 weeks of development time with risk of breaking existing functionality
4. **Current architecture works well** - Authentication, RLS, and data model are all functional

**Recommended Action Plan:**
1. ✅ **Immediate:** Implement PostgreSQL full-text search (`tsvector`/`tsquery`)
2. ✅ **Short-term (1-2 weeks):** Add `pg_vector` extension for semantic search
3. ⚠️ **Future (if needed):** Consider hybrid approach with Firestore for large documents

**Estimated Enhancement Effort:** 1-2 weeks (vs 2-4 weeks for full migration)

**Cost Savings:** $50-150/month compared to MongoDB Atlas or Firestore + Algolia

---

## Appendices

### A. Current Prompt Vault Schema

```sql
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    description TEXT,
    category TEXT,
    tags TEXT[] DEFAULT '{}',
    is_public BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### B. Recommended Enhanced Schema

```sql
-- Full-text search column
ALTER TABLE prompts 
ADD COLUMN search_vector tsvector 
GENERATED ALWAYS AS (
  to_tsvector('english', 
    coalesce(title, '') || ' ' || 
    coalesce(content, '') || ' ' || 
    coalesce(description, '')
  )
) STORED;

-- Vector embedding for semantic search
ALTER TABLE prompts ADD COLUMN embedding vector(1536);

-- Indexes
CREATE INDEX prompts_search_vector_idx ON prompts USING GIN(search_vector);
CREATE INDEX prompts_embedding_idx ON prompts USING ivfflat (embedding vector_cosine_ops);
```

### C. Search Query Examples

**Full-Text Search:**
```sql
SELECT * FROM prompts 
WHERE search_vector @@ to_tsquery('english', 'prompt & engineering')
ORDER BY ts_rank(search_vector, to_tsquery('english', 'prompt & engineering')) DESC;
```

**Semantic Search:**
```sql
SELECT *, embedding <=> '[0.1, 0.2, ...]'::vector AS distance
FROM prompts
WHERE embedding IS NOT NULL
ORDER BY embedding <=> '[0.1, 0.2, ...]'::vector
LIMIT 10;
```

---

**Research Completed By:** AI Assistant  
**Review Status:** Ready for Review  
**Next Steps:** Implement Phase 1 enhancements (full-text search optimization)

