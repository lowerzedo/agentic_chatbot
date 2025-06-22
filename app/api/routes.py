from flask import request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from app.api import api_bp
from app.models import Document, UniversityInfo
from app.services.rag_service import RAGService
from app import db
import logging

# Initialize RAG service
rag_service = None

def get_rag_service():
    """Get or create RAG service instance."""
    global rag_service
    if rag_service is None:
        rag_service = RAGService()
    return rag_service

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@api_bp.route('/university-info', methods=['GET'])
def get_university_info():
    """Get university information."""
    try:
        # Get the first university info record (assuming single university setup)
        university = UniversityInfo.query.first()
        
        if not university:
            return jsonify({
                'error': 'University information not configured'
            }), 404
        
        return jsonify({
            'university_name': university.university_name,
            'university_code': university.university_code,
            'contact_email': university.contact_email,
            'contact_phone': university.contact_phone,
            'website': university.website,
            'address': university.address,
            'welcome_message': university.welcome_message,
            'application_deadline': university.application_deadline.isoformat() if university.application_deadline else None
        })
        
    except Exception as e:
        logging.error(f"Error getting university info: {str(e)}")
        return jsonify({'error': 'Failed to retrieve university information'}), 500

@api_bp.route('/upload-document', methods=['POST'])
def upload_document():
    """Upload and process a PDF document for RAG."""
    try:
        # Check if file is present in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Validate file type
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Get optional metadata
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        category = request.form.get('category', 'general')
        
        # Secure filename and create unique filename
        original_filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{original_filename}"
        
        # Ensure upload directory exists
        upload_folder = current_app.config['UPLOAD_FOLDER']
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # Save file
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create document record
        document = Document(
            filename=unique_filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            file_type='pdf',
            title=title if title else original_filename,
            description=description,
            category=category
        )
        
        db.session.add(document)
        db.session.commit()
        
        # Process document asynchronously (for now, synchronously)
        try:
            rag_service = get_rag_service()
            success = rag_service.process_pdf_document(
                file_path=file_path,
                document_id=document.id,
                metadata={
                    'title': document.title,
                    'category': document.category,
                    'original_filename': document.original_filename
                }
            )
            
            if success:
                return jsonify({
                    'message': 'Document uploaded and processed successfully',
                    'document_id': document.id,
                    'filename': original_filename
                }), 201
            else:
                return jsonify({
                    'error': 'Document uploaded but processing failed',
                    'document_id': document.id
                }), 500
                
        except Exception as processing_error:
            logging.error(f"Error processing document: {str(processing_error)}")
            return jsonify({
                'error': 'Document uploaded but processing failed',
                'document_id': document.id,
                'details': str(processing_error)
            }), 500
        
    except Exception as e:
        logging.error(f"Error uploading document: {str(e)}")
        return jsonify({'error': 'Failed to upload document'}), 500

@api_bp.route('/documents', methods=['GET'])
def list_documents():
    """List all uploaded documents."""
    try:
        documents = Document.query.order_by(Document.uploaded_at.desc()).all()
        
        document_list = []
        for doc in documents:
            document_list.append({
                'id': doc.id,
                'title': doc.title,
                'original_filename': doc.original_filename,
                'category': doc.category,
                'file_size': doc.file_size,
                'is_processed': doc.is_processed,
                'chunk_count': doc.chunk_count,
                'uploaded_at': doc.uploaded_at.isoformat(),
                'processed_at': doc.processed_at.isoformat() if doc.processed_at else None
            })
        
        return jsonify({
            'documents': document_list,
            'total_count': len(document_list)
        })
        
    except Exception as e:
        logging.error(f"Error listing documents: {str(e)}")
        return jsonify({'error': 'Failed to retrieve documents'}), 500

@api_bp.route('/documents/<document_id>', methods=['DELETE'])
def delete_document(document_id):
    """Delete a document and its vector embeddings."""
    try:
        document = Document.query.get(document_id)
        
        if not document:
            return jsonify({'error': 'Document not found'}), 404
        
        # Delete vector embeddings
        rag_service = get_rag_service()
        rag_service.delete_document_chunks(document_id)
        
        # Delete physical file
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        # Delete database record
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({'message': 'Document deleted successfully'})
        
    except Exception as e:
        logging.error(f"Error deleting document: {str(e)}")
        return jsonify({'error': 'Failed to delete document'}), 500

@api_bp.route('/vector-stats', methods=['GET'])
def get_vector_stats():
    """Get vector database statistics."""
    try:
        rag_service = get_rag_service()
        stats = rag_service.get_collection_stats()
        
        # Also get database stats
        total_documents = Document.query.count()
        processed_documents = Document.query.filter_by(is_processed=True).count()
        
        return jsonify({
            'vector_database': stats,
            'database': {
                'total_documents': total_documents,
                'processed_documents': processed_documents,
                'unprocessed_documents': total_documents - processed_documents
            }
        })
        
    except Exception as e:
        logging.error(f"Error getting vector stats: {str(e)}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500 