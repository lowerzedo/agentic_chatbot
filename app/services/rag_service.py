import os
import logging
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import PyPDF2
from flask import current_app
from app.models import Document
from app import db

class RAGService:
    """Service class for Retrieval-Augmented Generation functionality."""
    
    def __init__(self):
        """Initialize the RAG service with embedding model and vector database."""
        self.embedding_model = None
        self.chroma_client = None
        self.collection = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize embedding model and vector database."""
        try:
            # Initialize sentence transformer for embeddings
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logging.info("Embedding model initialized successfully")
            
            # Initialize ChromaDB
            vector_db_path = current_app.config.get('VECTOR_DB_PATH', './vector_db')
            self.chroma_client = chromadb.PersistentClient(
                path=vector_db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="university_documents",
                metadata={"description": "University documents for RAG"}
            )
            
            logging.info("Vector database initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize RAG components: {str(e)}")
            raise
    
    def process_pdf_document(self, file_path: str, document_id: str, 
                           metadata: Optional[Dict] = None) -> bool:
        """
        Process a PDF document and store its chunks in the vector database.
        
        Args:
            file_path (str): Path to the PDF file
            document_id (str): Unique identifier for the document
            metadata (Dict, optional): Additional metadata for the document
            
        Returns:
            bool: True if processing was successful
        """
        try:
            # Extract text from PDF
            text_chunks = self._extract_text_from_pdf(file_path)
            
            if not text_chunks:
                logging.warning(f"No text extracted from PDF: {file_path}")
                return False
            
            # Create chunks with metadata
            chunk_ids = []
            chunk_texts = []
            chunk_metadatas = []
            
            for i, chunk in enumerate(text_chunks):
                chunk_id = f"{document_id}_chunk_{i}"
                chunk_ids.append(chunk_id)
                chunk_texts.append(chunk)
                
                chunk_metadata = {
                    'document_id': document_id,
                    'chunk_index': i,
                    'source_file': file_path
                }
                
                if metadata:
                    chunk_metadata.update(metadata)
                
                chunk_metadatas.append(chunk_metadata)
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(chunk_texts).tolist()
            
            # Store in vector database
            self.collection.add(
                ids=chunk_ids,
                embeddings=embeddings,
                documents=chunk_texts,
                metadatas=chunk_metadatas
            )
            
            # Update document record
            document = Document.query.get(document_id)
            if document:
                document.is_processed = True
                document.chunk_count = len(text_chunks)
                db.session.commit()
            
            logging.info(f"Successfully processed document {document_id} with {len(text_chunks)} chunks")
            return True
            
        except Exception as e:
            logging.error(f"Error processing PDF document {document_id}: {str(e)}")
            return False
    
    def search_similar_documents(self, query: str, n_results: int = 5, 
                               filter_metadata: Optional[Dict] = None) -> List[Dict]:
        """
        Search for similar documents based on the query.
        
        Args:
            query (str): Search query
            n_results (int): Number of results to return
            filter_metadata (Dict, optional): Metadata filters
            
        Returns:
            List[Dict]: List of similar document chunks with metadata
        """
        try:
            if not self.collection:
                self._initialize_components()
            
            # Generate embedding for the query
            query_embedding = self.embedding_model.encode([query]).tolist()
            
            # Search in vector database
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                where=filter_metadata,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity_score': 1 - results['distances'][0][i]  # Convert distance to similarity
                    })
            
            return formatted_results
            
        except Exception as e:
            logging.error(f"Error searching similar documents: {str(e)}")
            return []
    
    def get_relevant_context(self, query: str, category_filter: Optional[str] = None) -> List[str]:
        """
        Get relevant context documents for a query.
        
        Args:
            query (str): User query
            category_filter (str, optional): Filter by document category
            
        Returns:
            List[str]: List of relevant document texts
        """
        try:
            # Prepare metadata filter
            metadata_filter = {}
            if category_filter:
                metadata_filter['category'] = category_filter
            
            # Search for similar documents
            results = self.search_similar_documents(
                query=query,
                n_results=current_app.config.get('TOP_K_RESULTS', 5),
                filter_metadata=metadata_filter if metadata_filter else None
            )
            
            # Extract text content only
            context_texts = [result['text'] for result in results]
            
            return context_texts
            
        except Exception as e:
            logging.error(f"Error getting relevant context: {str(e)}")
            return []
    
    def _extract_text_from_pdf(self, file_path: str) -> List[str]:
        """
        Extract and chunk text from a PDF file.
        
        Args:
            file_path (str): Path to the PDF file
            
        Returns:
            List[str]: List of text chunks
        """
        try:
            text_chunks = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Extract text from all pages
                full_text = ""
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                
                # Chunk the text
                if full_text.strip():
                    chunks = self._chunk_text(
                        full_text,
                        chunk_size=current_app.config.get('CHUNK_SIZE', 1000),
                        chunk_overlap=current_app.config.get('CHUNK_OVERLAP', 200)
                    )
                    text_chunks.extend(chunks)
            
            return text_chunks
            
        except Exception as e:
            logging.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            return []
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks.
        
        Args:
            text (str): Text to chunk
            chunk_size (int): Maximum size of each chunk
            chunk_overlap (int): Overlap between chunks
            
        Returns:
            List[str]: List of text chunks
        """
        try:
            chunks = []
            start = 0
            text_length = len(text)
            
            while start < text_length:
                # Calculate end position
                end = start + chunk_size
                
                # If this is not the last chunk, try to break at a sentence boundary
                if end < text_length:
                    # Look for sentence endings within the overlap area
                    look_back_start = max(start, end - chunk_overlap)
                    chunk_text = text[start:end]
                    
                    # Find the last sentence ending
                    for i in range(len(chunk_text) - 1, -1, -1):
                        if chunk_text[i] in '.!?':
                            end = start + i + 1
                            break
                
                # Extract chunk
                chunk = text[start:end].strip()
                if chunk:
                    chunks.append(chunk)
                
                # Move start position (with overlap)
                start = end - chunk_overlap if end < text_length else text_length
            
            return chunks
            
        except Exception as e:
            logging.error(f"Error chunking text: {str(e)}")
            return [text]  # Return original text as single chunk
    
    def delete_document_chunks(self, document_id: str) -> bool:
        """
        Delete all chunks for a specific document from the vector database.
        
        Args:
            document_id (str): Document ID to delete
            
        Returns:
            bool: True if deletion was successful
        """
        try:
            # Query for chunks with the document ID
            results = self.collection.get(
                where={"document_id": document_id},
                include=['ids']
            )
            
            if results['ids']:
                # Delete the chunks
                self.collection.delete(ids=results['ids'])
                logging.info(f"Deleted {len(results['ids'])} chunks for document {document_id}")
                return True
            
            return True  # No chunks to delete is also success
            
        except Exception as e:
            logging.error(f"Error deleting document chunks for {document_id}: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict:
        """
        Get statistics about the vector database collection.
        
        Returns:
            Dict: Collection statistics
        """
        try:
            count = self.collection.count()
            return {
                'total_chunks': count,
                'collection_name': self.collection.name
            }
            
        except Exception as e:
            logging.error(f"Error getting collection stats: {str(e)}")
            return {'total_chunks': 0, 'collection_name': 'unknown'} 