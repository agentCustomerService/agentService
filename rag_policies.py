"""
RAG System for Company Policies
Retrieves policies from PDF and provides them to agents
"""

import os
import json
from pathlib import Path
from typing import List, Optional
from datetime import datetime

try:
    from PyPDF2 import PdfReader
    from langchain_community.embeddings import OllamaEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain.schema import Document
except ImportError as e:
    print(f"Warning: Some dependencies not installed: {e}")

POLICIES_DIR = Path(__file__).parent / "policies"
POLICIES_DIR.mkdir(exist_ok=True)

VECTORDB_PATH = POLICIES_DIR / "vectordb"
VECTORDB_PATH.mkdir(exist_ok=True)

METADATA_FILE = POLICIES_DIR / "metadata.json"


def init_policies_dir():
    """Initialize policies directory structure."""
    POLICIES_DIR.mkdir(exist_ok=True)
    VECTORDB_PATH.mkdir(exist_ok=True)
    
    if not METADATA_FILE.exists():
        with open(METADATA_FILE, 'w') as f:
            json.dump({
                "created_at": datetime.utcnow().isoformat(),
                "policies": [],
                "last_updated": datetime.utcnow().isoformat()
            }, f, indent=2)


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        raise Exception(f"Error reading PDF: {str(e)}")


def split_text_into_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 100) -> List[str]:
    """Split text into manageable chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = splitter.split_text(text)
    return chunks


def create_embeddings():
    """Create embeddings using Ollama (compatible with current setup)."""
    try:
        embeddings = OllamaEmbeddings(model="llama3.1:8b")
        return embeddings
    except Exception as e:
        print(f"Warning: Could not initialize Ollama embeddings: {e}")
        return None


def load_policies_from_pdf(pdf_path: str, policy_name: str = None) -> dict:
    """
    Load policies from PDF and create vector store.
    
    Args:
        pdf_path: Path to PDF file
        policy_name: Optional name for the policy
        
    Returns:
        dict with status and metadata
    """
    init_policies_dir()
    
    if policy_name is None:
        policy_name = Path(pdf_path).stem
    
    try:
        # Extract text from PDF
        print(f"[RAG] Extracting text from {pdf_path}...")
        text = extract_text_from_pdf(pdf_path)
        
        # Split into chunks
        print(f"[RAG] Splitting text into chunks...")
        chunks = split_text_into_chunks(text)
        
        # Create documents
        documents = [
            Document(
                page_content=chunk,
                metadata={
                    "policy_name": policy_name,
                    "source": pdf_path,
                    "chunk_index": i
                }
            )
            for i, chunk in enumerate(chunks)
        ]
        
        # Create embeddings and vector store
        print(f"[RAG] Creating embeddings and vector store...")
        embeddings = create_embeddings()
        
        if embeddings is None:
            # Fallback: use basic string matching without embeddings
            print("[RAG] Using fallback vector store (no embeddings)")
            vectorstore = {
                "type": "fallback",
                "documents": documents,
                "chunks": chunks
            }
        else:
            vectorstore = FAISS.from_documents(documents, embeddings)
            vectorstore_path = VECTORDB_PATH / f"{policy_name}_store"
            vectorstore.save_local(str(vectorstore_path))
            print(f"[RAG] Vector store saved to {vectorstore_path}")
        
        # Update metadata
        metadata = json.load(open(METADATA_FILE, 'r'))
        metadata["policies"].append({
            "name": policy_name,
            "pdf_path": str(pdf_path),
            "loaded_at": datetime.utcnow().isoformat(),
            "chunks_count": len(chunks),
            "vectorstore_path": str(VECTORDB_PATH / f"{policy_name}_store")
        })
        metadata["last_updated"] = datetime.utcnow().isoformat()
        
        with open(METADATA_FILE, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return {
            "success": True,
            "policy_name": policy_name,
            "chunks_count": len(chunks),
            "message": f"Loaded {len(chunks)} chunks from {policy_name}"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to load policy: {str(e)}"
        }


def load_vectorstore(policy_name: str):
    """Load a previously saved vector store."""
    try:
        vectorstore_path = VECTORDB_PATH / f"{policy_name}_store"
        
        if not vectorstore_path.exists():
            print(f"[RAG] Vector store not found: {vectorstore_path}")
            return None
        
        embeddings = create_embeddings()
        if embeddings is None:
            print("[RAG] Cannot load vector store without embeddings")
            return None
        
        vectorstore = FAISS.load_local(str(vectorstore_path), embeddings)
        return vectorstore
        
    except Exception as e:
        print(f"[RAG] Error loading vector store: {e}")
        return None


def search_policies(query: str, policy_name: str = None, k: int = 3) -> List[str]:
    """
    Search for relevant policies based on query.
    
    Args:
        query: Search query
        policy_name: Optional specific policy to search
        k: Number of results to return
        
    Returns:
        List of relevant policy excerpts
    """
    try:
        metadata = json.load(open(METADATA_FILE, 'r'))
        policies = metadata.get("policies", [])
        
        if not policies:
            return []
        
        results = []
        
        # Load and search each policy
        for policy in policies:
            if policy_name and policy["name"] != policy_name:
                continue
            
            vectorstore = load_vectorstore(policy["name"])
            
            if vectorstore is None:
                # Fallback to basic text search
                print(f"[RAG] Fallback search for policy '{policy['name']}'")
                continue
            
            # Search for relevant documents
            try:
                docs = vectorstore.similarity_search(query, k=k)
                for doc in docs:
                    results.append({
                        "policy": policy["name"],
                        "content": doc.page_content,
                        "chunk_index": doc.metadata.get("chunk_index")
                    })
            except Exception as e:
                print(f"[RAG] Error searching policy '{policy['name']}': {e}")
        
        return results
        
    except Exception as e:
        print(f"[RAG] Error in search: {e}")
        return []


def get_cancellation_policies() -> str:
    """Get cancellation policies relevant to refunds."""
    results = search_policies(
        "cancellation policy refund cancel order",
        k=5
    )
    
    if not results:
        return "No specific cancellation policies found."
    
    policy_text = "📋 **CANCELLATION POLICIES:**\n\n"
    for i, result in enumerate(results, 1):
        policy_text += f"{i}. {result['content']}\n\n"
    
    return policy_text


def get_refund_policies() -> str:
    """Get refund policies."""
    results = search_policies(
        "refund policy refund amount refund process refund eligibility",
        k=5
    )
    
    if not results:
        return "No specific refund policies found."
    
    policy_text = "📋 **REFUND POLICIES:**\n\n"
    for i, result in enumerate(results, 1):
        policy_text += f"{i}. {result['content']}\n\n"
    
    return policy_text


def get_policies_context(action: str = "both") -> str:
    """
    Get policies context for the agent.
    
    Args:
        action: "cancellation", "refund", or "both"
        
    Returns:
        Formatted policy context
    """
    context = ""
    
    if action in ("cancellation", "both"):
        context += get_cancellation_policies() + "\n"
    
    if action in ("refund", "both"):
        context += get_refund_policies() + "\n"
    
    return context if context else "No policies available."


def list_loaded_policies() -> List[dict]:
    """List all loaded policies."""
    try:
        if not METADATA_FILE.exists():
            return []
        
        metadata = json.load(open(METADATA_FILE, 'r'))
        return metadata.get("policies", [])
        
    except Exception as e:
        print(f"[RAG] Error listing policies: {e}")
        return []


# Global vector store cache
_vectorstore_cache = {}


def get_or_load_vectorstore(policy_name: str):
    """Get or load vector store with caching."""
    if policy_name not in _vectorstore_cache:
        _vectorstore_cache[policy_name] = load_vectorstore(policy_name)
    return _vectorstore_cache[policy_name]


def clear_cache():
    """Clear vectorstore cache."""
    _vectorstore_cache.clear()
