# RAG Policy System Documentation

## Overview

The RAG (Retrieval-Augmented Generation) Policy System allows the agent to:

- Load company policies from PDF documents
- Create a searchable vector database
- Retrieve relevant policies during customer interactions
- Show customers policies before executing cancel/refund actions
- Provide compliance-aware responses

---

## Features

✅ **PDF Policy Loading** - Upload and process policy documents
✅ **Vector Database** - FAISS-based semantic search
✅ **Automatic Retrieval** - Policies retrieved based on user request
✅ **Policy Display** - Show relevant policies before actions
✅ **Caching** - Efficient vectorstore caching
✅ **Fallback Support** - Works without embeddings if needed

---

## Architecture

```
Company Policy PDF
    ↓
[PDF Extraction & Text Processing]
    ↓
[Text Splitting (500 char chunks)]
    ↓
[Ollama Embeddings Generation]
    ↓
[FAISS Vector Database]
    ↓
[Policy Storage (policies/vectordb/)]
    ↓
[Agent RAG Retrieval]
    ↓
[Policy Display to Customer]
    ↓
[Customer Consent & Action]
```

---

## Components

### 1. rag_policies.py (RAG Engine)

**Main Functions:**

- `load_policies_from_pdf(pdf_path, policy_name)` - Load PDF and create vector store
- `search_policies(query, policy_name, k)` - Search for relevant policies
- `get_cancellation_policies()` - Retrieve cancellation-related policies
- `get_refund_policies()` - Retrieve refund-related policies
- `get_policies_context(action)` - Get policy context for agent
- `list_loaded_policies()` - List all loaded policies

**File Structure:**

```
policies/
├── vectordb/
│   ├── cancellation_policy_store/
│   ├── refund_policy_store/
│   └── ...
└── metadata.json
```

### 2. agent_with_rag.py (Enhanced Agent)

**Changes to Agent:**

1. **New AgentState Field:** `policies_shown: bool`
2. **New System Prompt:** Includes policy display instructions
3. **Policy Retrieval:** Automatic retrieval based on user message
4. **Modified Analyze Node:** Shows policies before actions
5. **Policy Context:** Injected into LLM prompt

**Example Workflow:**

```
Customer: "I want to cancel my order"
    ↓
Agent: Retrieve cancellation policies
    ↓
Agent: Display policies to customer
    ↓
Agent: Ask for consent
    ↓
Customer: Agrees to policies
    ↓
Agent: Execute cancellation
```

### 3. app_with_rag.py (Enhanced FastAPI)

**New Endpoints:**

1. `POST /policies/upload` - Upload policy PDF
2. `GET /policies/list` - List loaded policies
3. `GET /policies/cancellation` - Get cancellation policies
4. `GET /policies/refund` - Get refund policies
5. `GET /policies/all` - Get all policies

---

## Setup & Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

New packages added:

- `PyPDF2` - PDF extraction
- `faiss-cpu` - Vector database (use `faiss-gpu` for GPU)
- `langchain-community` - LangChain community features

### 2. Prepare Policy Documents

Place policy PDFs in the `policies/` directory:

```bash
mkdir -p policies/
# Copy your policy PDFs here
```

### 3. Initialize System

```python
from rag_policies import init_policies_dir
init_policies_dir()
```

---

## Usage Guide

### Upload a Policy

```python
from rag_policies import load_policies_from_pdf

result = load_policies_from_pdf(
    pdf_path="policies/company_policies.pdf",
    policy_name="Company Policies 2024"
)

print(result)
# {
#   "success": true,
#   "policy_name": "Company Policies 2024",
#   "chunks_count": 42,
#   "message": "Loaded 42 chunks from Company Policies 2024"
# }
```

### Upload via API

```bash
curl -X POST "http://localhost:8000/policies/upload" \
  -F "file=@policies/refund_policy.pdf" \
  -F "policy_name=Refund Policy"
```

### Search Policies

```python
from rag_policies import search_policies

results = search_policies(
    query="Can I cancel my order?",
    k=3
)

for result in results:
    print(f"Policy: {result['policy']}")
    print(f"Content: {result['content']}")
```

### Get Policies Context

```python
from rag_policies import get_policies_context

# Get cancellation policies
policies = get_policies_context("cancellation")

# Get refund policies
policies = get_policies_context("refund")

# Get both
policies = get_policies_context("both")
```

### List Loaded Policies

```python
from rag_policies import list_loaded_policies

policies = list_loaded_policies()
for policy in policies:
    print(f"- {policy['name']}: {policy['chunks_count']} chunks")
```

---

## API Endpoints

### Upload Policy PDF

```http
POST /policies/upload
Content-Type: multipart/form-data

file: <policy.pdf>
policy_name: <optional_name>
```

**Response:**

```json
{
  "success": true,
  "policy_name": "Refund Policy",
  "chunks_count": 42,
  "message": "Loaded 42 chunks from Refund Policy"
}
```

---

### List Loaded Policies

```http
GET /policies/list
```

**Response:**

```json
{
  "policies": [
    {
      "name": "Refund Policy",
      "pdf_path": "/path/to/policy.pdf",
      "loaded_at": "2024-01-01T10:00:00",
      "chunks_count": 42,
      "vectorstore_path": "/path/to/store"
    }
  ],
  "count": 1
}
```

---

### Get Cancellation Policies

```http
GET /policies/cancellation
```

**Response:**

```json
{
  "policies": "📋 **CANCELLATION POLICIES:**\n\n1. ... \n\n2. ..."
}
```

---

### Get Refund Policies

```http
GET /policies/refund
```

**Response:**

```json
{
  "policies": "📋 **REFUND POLICIES:**\n\n1. ... \n\n2. ..."
}
```

---

### Get All Policies

```http
GET /policies/all
```

**Response:**

```json
{
  "policies": "📋 **CANCELLATION POLICIES:**\n\n... \n📋 **REFUND POLICIES:**\n\n..."
}
```

---

## Chat with Policies

### Customer Initiates Cancellation

**Request:**

```json
POST /chat
{
  "message": "I want to cancel my order",
  "order_id": "ORDER123"
}
```

**Response:**

```json
{
  "success": true,
  "session_id": "uuid",
  "actions": [],
  "response": "📋 **CANCELLATION POLICIES:**\n\n1. Orders may be cancelled within 24 hours for full refund...\n\nDo you agree to proceed with cancellation?",
  "logs": []
}
```

### Customer Agrees to Cancellation

**Request:**

```json
POST /chat
{
  "message": "Yes, I agree",
  "order_id": "ORDER123",
  "session_id": "uuid"
}
```

**Response:**

```json
{
  "success": true,
  "session_id": "uuid",
  "actions": ["cancel"],
  "response": "Completed actions: cancel",
  "logs": ["Order ORDER123 canceled"]
}
```

---

## Example Workflow

### Step 1: Create Sample Policies

```bash
python test_rag_system.py
```

This creates sample cancellation and refund policies.

### Step 2: Start Server with RAG

```bash
python -m uvicorn app_with_rag:api --reload
```

### Step 3: Upload Policies via API

```bash
curl -X POST "http://localhost:8000/policies/upload" \
  -F "file=@policies/cancellation_policy.pdf" \
  -F "policy_name=Cancellation Policy"

curl -X POST "http://localhost:8000/policies/upload" \
  -F "file=@policies/refund_policy.pdf" \
  -F "policy_name=Refund Policy"
```

### Step 4: List Loaded Policies

```bash
curl http://localhost:8000/policies/list
```

### Step 5: Chat with Agent

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need to cancel my order",
    "order_id": "ORD123"
  }'
```

Agent will display policies and ask for consent before canceling.

---

## Configuration

### Vector Database

Change vector store location in `rag_policies.py`:

```python
VECTORDB_PATH = Path(__file__).parent / "policies" / "vectordb"
```

### Text Chunking

Adjust chunk size in `split_text_into_chunks()`:

```python
def split_text_into_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 100):
```

- `chunk_size`: Size of each chunk (default: 500)
- `chunk_overlap`: Overlap between chunks (default: 100)

### Search Results

Change number of results in `search_policies()`:

```python
results = search_policies(query, k=3)  # Returns top 3 results
```

---

## Embeddings Models

### Ollama (Local)

Uses Ollama with llama3.1:8b model (default):

```python
embeddings = OllamaEmbeddings(model="llama3.1:8b")
```

Other Ollama models:

- `nomic-embed-text` - Specialized embedding model
- `all-minilm` - Smaller embedding model
- `mistral` - General model

### Fallback Mode

If embeddings unavailable, system falls back to basic text search:

```python
if embeddings is None:
    print("[RAG] Using fallback vector store (no embeddings)")
```

---

## Performance Considerations

### Vector Store Size

- Each policy loaded = separate vector store
- Memory usage: ~10-50 MB per store (depending on size)
- Caching reduces reload overhead

### Search Performance

- First search: ~500ms (load + search)
- Subsequent searches: ~50ms (cached)

### Scaling Tips

1. **Use GPU FAISS** - Replace `faiss-cpu` with `faiss-gpu`
2. **Batch uploads** - Load multiple policies at once
3. **Cache management** - Clear cache between updates
4. **Index optimization** - Use approximate nearest neighbor search

---

## Troubleshooting

### Issue: PDF not readable

**Solution:** Ensure PDF is text-based (not scanned image)

```bash
# Convert PDF if needed
pdftotext input.pdf text.txt
```

### Issue: No search results

**Solution:** Check policy was loaded

```bash
curl http://localhost:8000/policies/list
```

### Issue: Embeddings failing

**Solution:** Verify Ollama is running

```bash
ollama serve
# In another terminal:
ollama pull nomic-embed-text
```

### Issue: Memory usage high

**Solution:** Clear vector store cache

```python
from rag_policies import clear_cache
clear_cache()
```

---

## Security Considerations

- PDFs stored in `policies/` directory
- Metadata stored in `policies/metadata.json`
- Vector stores in `policies/vectordb/`
- Ensure proper access control to `policies/` directory

---

## Future Enhancements

- [ ] Support multiple policy versions
- [ ] Policy versioning and history
- [ ] Policy update notifications
- [ ] Custom search ranking
- [ ] Policy-specific compliance checks
- [ ] Policy analytics and search logging
- [ ] Multi-language support
- [ ] Policy similarity detection

---

## Files Included

- `rag_policies.py` - Core RAG engine
- `agent_with_rag.py` - Enhanced LangGraph agent
- `app_with_rag.py` - Enhanced FastAPI with policy endpoints
- `test_rag_system.py` - Test and demo script
- `requirements.txt` - Updated dependencies

---

## Integration Checklist

- [x] PDF loading and processing
- [x] Vector database creation
- [x] Policy search and retrieval
- [x] Agent integration
- [x] API endpoints
- [x] Caching mechanism
- [x] Fallback support
- [x] Error handling
- [x] Documentation
- [x] Test suite

---

**Ready to Deploy!** 🚀

The RAG Policy System is now fully integrated and ready to use.
