from flask import request, jsonify, current_app
import uuid
from datetime import datetime
from app.chat import chat_bp
from app.models import ChatSession, ChatMessage, UniversityInfo, ApplicantData
from app.services.gemini_service import GeminiService
from app.services.rag_service import RAGService
from app import db
import logging
import re

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

@chat_bp.route('/applicant-data', methods=['POST'])
def save_applicant_data():
    """Save applicant data before starting chat."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Validate required fields (intended_program is optional initially)
        required_fields = ['name', 'email', 'phone']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing_fields': missing_fields
            }), 400
        
        # Validate email format
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.match(email_pattern, data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Create chat session first
        session_id = str(uuid.uuid4())
        chat_session = ChatSession(session_id=session_id)
        db.session.add(chat_session)
        db.session.flush()  # Get the session ID without committing
        
        # Create applicant data
        applicant_data = ApplicantData(
            session_id=chat_session.id,
            name=data['name'].strip(),
            email=data['email'].strip().lower(),
            phone=data['phone'].strip(),
            intended_program=data.get('intended_program', '').strip() if data.get('intended_program') else None,
            application_status='interested',
            data_collection_status='basic_info_complete'  # Changed status since program not selected yet
        )
        
        db.session.add(applicant_data)
        db.session.commit()
        
        return jsonify({
            'message': 'Applicant data saved successfully',
            'session_id': session_id,
            'applicant_data': applicant_data.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error saving applicant data: {str(e)}")
        return jsonify({'error': 'Failed to save applicant data'}), 500

@chat_bp.route('/applicant-data/<session_id>', methods=['PUT'])
def update_applicant_data(session_id):
    """Update existing applicant data."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Request data is required'}), 400
        
        # Find session
        session = ChatSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        # Find applicant data
        applicant_data = ApplicantData.query.filter_by(session_id=session.id).first()
        if not applicant_data:
            return jsonify({'error': 'Applicant data not found'}), 404
        
        # Update fields if provided
        if 'name' in data and data['name']:
            applicant_data.name = data['name'].strip()
        if 'email' in data and data['email']:
            # Validate email format
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            if not re.match(email_pattern, data['email']):
                return jsonify({'error': 'Invalid email format'}), 400
            applicant_data.email = data['email'].strip().lower()
        if 'phone' in data and data['phone']:
            applicant_data.phone = data['phone'].strip()
        if 'intended_program' in data and data['intended_program']:
            applicant_data.intended_program = data['intended_program'].strip()
        
        # Update status
        if all([applicant_data.name, applicant_data.email, applicant_data.phone, applicant_data.intended_program]):
            applicant_data.data_collection_status = 'complete'
        
        applicant_data.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'message': 'Applicant data updated successfully',
            'applicant_data': applicant_data.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error updating applicant data: {str(e)}")
        return jsonify({'error': 'Failed to update applicant data'}), 500

def detect_application_intent(message):
    """Detect if user wants to apply."""
    application_keywords = [
        'apply', 'application', 'enroll', 'admission', 'register',
        'how to apply', 'want to apply', 'interested in applying',
        'admission process', 'enrollment'
    ]
    return any(keyword in message.lower() for keyword in application_keywords)

def extract_program_info(message, gemini_service=None):
    """Extract program information from message using AI."""
    if not gemini_service:
        return None
        
    try:
        extraction_prompt = f"""
Extract the academic program the user is interested in from this message. Return ONLY a JSON object:

Message: "{message}"

Extract:
- intended_program: The specific academic program they want to apply for

Rules:
- Only extract if user shows clear intent to apply or enroll
- Look for program names, degrees, or fields of study
- Format as "Program Name" (e.g., "Cybersecurity Program", "Computer Science Program")
- Return null if no program is mentioned

Return format: {{"intended_program": "value or null"}}
"""
        
        response = gemini_service.model.generate_content(extraction_prompt)
        
        if response and response.text:
            import json
            try:
                ai_extracted = json.loads(response.text.strip())
                program = ai_extracted.get('intended_program')
                
                if program and program != 'null':
                    return program
                        
            except (json.JSONDecodeError, KeyError) as e:
                logging.warning(f"Failed to parse AI program extraction: {e}")
                
    except Exception as e:
        logging.error(f"Error in AI program extraction: {e}")
    
    # Fallback regex for program
    program_patterns = [
        r'apply.*?for.*?(cybersecurity.*?program)',
        r'apply.*?for.*?(computer science.*?program)', 
        r'apply.*?for.*?(engineering.*?program)',
        r'apply.*?for.*?(business.*?program)',
        r'interested in.*?(cybersecurity.*?program)',
        r'interested in.*?(computer science.*?program)',
        r'enroll.*?in.*?(cybersecurity.*?program)',
        r'(cybersecurity program)',
        r'(computer science program)',
    ]
    
    for pattern in program_patterns:
        program_match = re.search(pattern, message.lower())
        if program_match:
            program = program_match.group(1).strip().title()
            if 'program' not in program.lower():
                program += ' Program'
            return program
    
    return None

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
        
        # Get existing applicant data (user data should be pre-saved)
        applicant_data = ApplicantData.query.filter_by(session_id=session.id).first()
        
        # Check for application intent and extract program info
        has_application_intent = detect_application_intent(user_message)
        
        # Check if application intent was captured and generate appropriate response
        application_recorded = False
        if has_application_intent and applicant_data and not applicant_data.intended_program:
            # Extract program information using AI
            program = extract_program_info(user_message, gemini_svc)
            
            if program:
                applicant_data.intended_program = program
                applicant_data.application_status = 'applying'
                applicant_data.data_collection_status = 'complete'
                db.session.commit()
                application_recorded = True
                
                logging.info(f"Updated applicant program intent: {applicant_data.intended_program} for session {session_id}")
        
        # Get relevant context from RAG
        context_documents = rag_svc.get_relevant_context(user_message)
        
        # Generate response with application confirmation if needed
        if application_recorded:
            # Generate a response that confirms application intent and provides program info
            confirmation_message = f"""
✅ **Application Intent Recorded!**

Thank you for your interest in applying to **{applicant_data.intended_program}**! I've recorded your application intent and your information:

👤 **Your Details:**
• Name: {applicant_data.name}
• Email: {applicant_data.email}
• Phone: {applicant_data.phone}
• Program: {applicant_data.intended_program}

Now let me provide you with specific information about this program and the application process.

"""
            
            # Get RAG response for additional program information
            rag_response = gemini_svc.generate_rag_response(
                query=user_message,
                context_documents=context_documents
            )
            
            # Combine confirmation with program information
            response = {
                'text': confirmation_message + rag_response['text'],
                'sources': rag_response.get('sources', []),
                'confidence': rag_response.get('confidence', 1.0)
            }
        else:
            # Regular RAG response
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
        
        response_data = {
            'message_id': assistant_msg.id,
            'response': assistant_msg.content,
            'confidence_score': assistant_msg.confidence_score
        }
        
        # Add applicant data if available
        if applicant_data:
            response_data['applicant_data'] = applicant_data.to_dict()
        
        return jsonify(response_data)
        
    except Exception as e:
        logging.error(f"Error processing message: {str(e)}")
        return jsonify({'error': 'Failed to process message'}), 500

@chat_bp.route('/session/<session_id>/applicant-data', methods=['GET'])
def get_applicant_data(session_id):
    """Get applicant data for a session."""
    try:
        session = ChatSession.query.filter_by(session_id=session_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404
        
        applicant_data = ApplicantData.query.filter_by(session_id=session.id).first()
        if not applicant_data:
            return jsonify({'applicant_data': None}), 200
        
        return jsonify({'applicant_data': applicant_data.to_dict()}), 200
        
    except Exception as e:
        logging.error(f"Error getting applicant data: {str(e)}")
        return jsonify({'error': 'Failed to get applicant data'}), 500 