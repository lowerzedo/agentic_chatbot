from flask import request, jsonify, current_app
import uuid
from datetime import datetime
from app.chat import chat_bp
from app.models import ChatSession, ChatMessage, UniversityInfo
from app.services.gemini_service import GeminiService
from app.services.rag_service import RAGService
from app import db
import logging

# Initialize services
gemini_service = None
rag_service = None

def get_services():
    """Get or create service instances."""
    global gemini_service, rag_service
    if gemini_service is None:
        gemini_service = GeminiService()
    if rag_service is None:
        rag_service = RAGService()
    return gemini_service, rag_service

@chat_bp.route('/session', methods=['POST'])
def create_chat_session():
    """Create a new chat session."""
    try:
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        
        # Create session record
        chat_session = ChatSession(session_id=session_id)
        db.session.add(chat_session)
        db.session.commit()
        
        # Get university welcome message
        university = UniversityInfo.query.first()
        welcome_message = "Hello! I'm here to help you with information about our university. How can I assist you today?"
        
        if university and university.welcome_message:
            welcome_message = university.welcome_message
        
        return jsonify({
            'session_id': session_id,
            'message': 'Chat session created successfully',
            'welcome_message': welcome_message
        }), 201
        
    except Exception as e:
        logging.error(f"Error creating chat session: {str(e)}")
        return jsonify({'error': 'Failed to create chat session'}), 500

@chat_bp.route('/session/<session_id>/message', methods=['POST'])
def send_message(session_id):
    """Send a message and get AI response."""
    try:
        # Get request data
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message content is required'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        # Find session
        session = ChatSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Get services
        gemini_svc, rag_svc = get_services()
        
        # Save user message
        user_msg = ChatMessage(
            session_id=session.id,
            message_type='user',
            content=user_message
        )
        db.session.add(user_msg)
        db.session.commit()
        
        # Get relevant context from RAG
        context_documents = rag_svc.get_relevant_context(user_message)
        
        # Generate response using RAG
        response = gemini_svc.generate_rag_response(
            query=user_message,
            context_documents=context_documents
        )
        
        # Save assistant response
        assistant_msg = ChatMessage(
            session_id=session.id,
            message_type='assistant',
            content=response['text'],
            source_documents=response.get('sources', []),
            confidence_score=response.get('confidence', 0.0)
        )
        
        db.session.add(assistant_msg)
        db.session.commit()
        
        return jsonify({
            'message_id': assistant_msg.id,
            'response': assistant_msg.content,
            'confidence_score': assistant_msg.confidence_score
        })
        
    except Exception as e:
        logging.error(f"Error processing message: {str(e)}")
        return jsonify({'error': 'Failed to process message'}), 500 