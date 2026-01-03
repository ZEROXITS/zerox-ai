"""
RAG (Retrieval Augmented Generation) Service
Upload documents and chat with them
"""
import os
import hashlib
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import httpx
import re

# Document processing
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


class TextSplitter:
    """Split text into chunks for embedding"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        if not text:
            return []
        
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end
                for sep in ['. ', '! ', '? ', '\n']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep > start:
                        end = last_sep + 1
                        break
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - self.chunk_overlap
        
        return chunks


class DocumentProcessor:
    """Process different document types"""
    
    @staticmethod
    async def process_text(content: str) -> str:
        """Process plain text"""
        return content
    
    @staticmethod
    async def process_pdf(file_path: str) -> str:
        """Extract text from PDF"""
        try:
            import PyPDF2
            
            text = ""
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            
            return text
        except ImportError:
            # Fallback: try pdfplumber
            try:
                import pdfplumber
                
                text = ""
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ""
                        text += "\n"
                
                return text
            except:
                return ""
        except Exception as e:
            return f"Error processing PDF: {str(e)}"
    
    @staticmethod
    async def process_docx(file_path: str) -> str:
        """Extract text from DOCX"""
        try:
            from docx import Document
            
            doc = Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            
            return text
        except Exception as e:
            return f"Error processing DOCX: {str(e)}"
    
    @staticmethod
    async def process_markdown(content: str) -> str:
        """Process markdown - remove formatting"""
        # Remove code blocks
        content = re.sub(r'```[\s\S]*?```', '', content)
        # Remove inline code
        content = re.sub(r'`[^`]+`', '', content)
        # Remove links but keep text
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
        # Remove images
        content = re.sub(r'!\[([^\]]*)\]\([^\)]+\)', '', content)
        # Remove headers markers
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
        # Remove bold/italic
        content = re.sub(r'\*+([^*]+)\*+', r'\1', content)
        
        return content
    
    @staticmethod
    async def process_csv(file_path: str) -> str:
        """Convert CSV to text"""
        try:
            import csv
            
            text = ""
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader, [])
                
                for row in reader:
                    row_text = ", ".join(f"{h}: {v}" for h, v in zip(headers, row) if v)
                    text += row_text + "\n"
            
            return text
        except Exception as e:
            return f"Error processing CSV: {str(e)}"
    
    @staticmethod
    async def process_json(file_path: str) -> str:
        """Convert JSON to text"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            def flatten_json(obj, prefix=""):
                text = ""
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        text += flatten_json(v, f"{prefix}{k}: ")
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        text += flatten_json(item, f"{prefix}[{i}] ")
                else:
                    text += f"{prefix}{obj}\n"
                return text
            
            return flatten_json(data)
        except Exception as e:
            return f"Error processing JSON: {str(e)}"


class EmbeddingService:
    """Generate embeddings using free models"""
    
    def __init__(self, model: str = "sentence-transformers"):
        self.model = model
        self._local_model = None
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding for text"""
        # Try local model first (sentence-transformers)
        try:
            return await self._get_local_embedding(text)
        except:
            # Fallback to simple hash-based embedding (for demo)
            return self._get_simple_embedding(text)
    
    async def _get_local_embedding(self, text: str) -> List[float]:
        """Use sentence-transformers locally"""
        try:
            from sentence_transformers import SentenceTransformer
            
            if self._local_model is None:
                self._local_model = SentenceTransformer('all-MiniLM-L6-v2')
            
            embedding = self._local_model.encode(text)
            return embedding.tolist()
        except ImportError:
            raise Exception("sentence-transformers not installed")
    
    def _get_simple_embedding(self, text: str, dim: int = 384) -> List[float]:
        """Simple hash-based embedding (fallback)"""
        import hashlib
        import math
        
        # Create deterministic embedding from text
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        
        embedding = []
        for i in range(dim):
            # Use different parts of hash for each dimension
            idx = (i * 2) % len(text_hash)
            val = int(text_hash[idx:idx+2], 16) / 255.0 - 0.5
            embedding.append(val)
        
        # Normalize
        norm = math.sqrt(sum(x*x for x in embedding))
        if norm > 0:
            embedding = [x/norm for x in embedding]
        
        return embedding
    
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for multiple texts"""
        return [await self.get_embedding(text) for text in texts]


class VectorStore:
    """Simple in-memory vector store with cosine similarity"""
    
    def __init__(self):
        self.vectors: Dict[str, Dict[str, Any]] = {}
    
    def add(self, doc_id: str, chunk_id: str, embedding: List[float], content: str, metadata: Dict = None):
        """Add a vector to the store"""
        key = f"{doc_id}_{chunk_id}"
        self.vectors[key] = {
            "doc_id": doc_id,
            "chunk_id": chunk_id,
            "embedding": embedding,
            "content": content,
            "metadata": metadata or {}
        }
    
    def search(self, query_embedding: List[float], doc_ids: List[str] = None, top_k: int = 5) -> List[Dict]:
        """Search for similar vectors"""
        results = []
        
        for key, data in self.vectors.items():
            # Filter by doc_ids if specified
            if doc_ids and data["doc_id"] not in doc_ids:
                continue
            
            similarity = self._cosine_similarity(query_embedding, data["embedding"])
            results.append({
                "doc_id": data["doc_id"],
                "chunk_id": data["chunk_id"],
                "content": data["content"],
                "metadata": data["metadata"],
                "score": similarity
            })
        
        # Sort by similarity
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
    
    def delete_document(self, doc_id: str):
        """Delete all vectors for a document"""
        keys_to_delete = [k for k, v in self.vectors.items() if v["doc_id"] == doc_id]
        for key in keys_to_delete:
            del self.vectors[key]
    
    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        import math
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)


class RAGService:
    """Main RAG service"""
    
    def __init__(self):
        self.text_splitter = TextSplitter()
        self.embedding_service = EmbeddingService()
        self.vector_store = VectorStore()
        self.processor = DocumentProcessor()
    
    async def process_document(
        self,
        file_path: str,
        doc_id: str,
        file_type: str,
        metadata: Dict = None
    ) -> Dict[str, Any]:
        """Process a document and store embeddings"""
        
        # Extract text based on file type
        if file_type == "pdf":
            text = await self.processor.process_pdf(file_path)
        elif file_type == "docx":
            text = await self.processor.process_docx(file_path)
        elif file_type == "csv":
            text = await self.processor.process_csv(file_path)
        elif file_type == "json":
            text = await self.processor.process_json(file_path)
        elif file_type in ["md", "markdown"]:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = await self.processor.process_markdown(f.read())
        else:
            # Plain text
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        
        if not text or text.startswith("Error"):
            return {"success": False, "error": text or "Could not extract text"}
        
        # Split into chunks
        chunks = self.text_splitter.split(text)
        
        if not chunks:
            return {"success": False, "error": "No content to process"}
        
        # Generate embeddings and store
        for i, chunk in enumerate(chunks):
            embedding = await self.embedding_service.get_embedding(chunk)
            self.vector_store.add(
                doc_id=doc_id,
                chunk_id=str(i),
                embedding=embedding,
                content=chunk,
                metadata={**(metadata or {}), "chunk_index": i}
            )
        
        return {
            "success": True,
            "doc_id": doc_id,
            "chunks": len(chunks),
            "total_chars": len(text)
        }
    
    async def query(
        self,
        query: str,
        doc_ids: List[str] = None,
        top_k: int = 5
    ) -> List[Dict]:
        """Query the vector store"""
        
        # Get query embedding
        query_embedding = await self.embedding_service.get_embedding(query)
        
        # Search
        results = self.vector_store.search(
            query_embedding=query_embedding,
            doc_ids=doc_ids,
            top_k=top_k
        )
        
        return results
    
    async def get_context(
        self,
        query: str,
        doc_ids: List[str] = None,
        max_tokens: int = 2000
    ) -> str:
        """Get relevant context for a query"""
        
        results = await self.query(query, doc_ids, top_k=10)
        
        context_parts = []
        total_chars = 0
        max_chars = max_tokens * 4  # Approximate
        
        for result in results:
            if total_chars + len(result["content"]) > max_chars:
                break
            context_parts.append(result["content"])
            total_chars += len(result["content"])
        
        return "\n\n".join(context_parts)
    
    def delete_document(self, doc_id: str):
        """Delete a document from the store"""
        self.vector_store.delete_document(doc_id)


# Global RAG service instance
rag_service = RAGService()
