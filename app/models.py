from app import db
from datetime import datetime, timezone
import uuid
from enum import Enum

class ApplicationStatus(Enum):
    """Enumeration for application status."""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WAITING_FOR_DOCUMENTS = "waiting_for_documents"

class ChatSession(db.Model):
    """Model for chat sessions."""
    
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationship to messages
    messages = db.relationship('ChatMessage', backref='session', lazy=True, cascade='all, delete-orphan')
    
    # Relationship to applications
    applications = db.relationship('Application', backref='chat_session', lazy=True)

class ChatMessage(db.Model):
    """Model for individual chat messages."""
    
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('chat_sessions.id'), nullable=False)
    message_type = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # Additional metadata for RAG
    source_documents = db.Column(db.JSON)  # Store references to source documents used
    confidence_score = db.Column(db.Float)

class Application(db.Model):
    """Model for university applications."""
    
    __tablename__ = 'applications'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.String(36), db.ForeignKey('chat_sessions.id'), nullable=False)
    
    # Personal Information
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    date_of_birth = db.Column(db.Date)
    
    # Address Information
    address_line1 = db.Column(db.String(255))
    address_line2 = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    postal_code = db.Column(db.String(20))
    country = db.Column(db.String(100))
    
    # Academic Information
    program_interest = db.Column(db.String(200))
    previous_education = db.Column(db.Text)
    gpa = db.Column(db.Float)
    test_scores = db.Column(db.JSON)  # Store SAT, GRE, etc. scores
    
    # Application Metadata
    status = db.Column(db.Enum(ApplicationStatus), default=ApplicationStatus.PENDING)
    submitted_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Agent Processing Information
    agent_notes = db.Column(db.Text)  # Notes from the AI agent
    missing_information = db.Column(db.JSON)  # List of missing required fields
    
    # Admin Notes
    admin_notes = db.Column(db.Text)
    reviewed_by = db.Column(db.String(100))
    reviewed_at = db.Column(db.DateTime)

class Document(db.Model):
    """Model for university documents used in RAG."""
    
    __tablename__ = 'documents'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))
    
    # Document Metadata
    title = db.Column(db.String(500))
    description = db.Column(db.Text)
    category = db.Column(db.String(100))  # e.g., 'admission', 'courses', 'policies'
    
    # Processing Status
    is_processed = db.Column(db.Boolean, default=False)
    processed_at = db.Column(db.DateTime)
    chunk_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

class UniversityInfo(db.Model):
    """Model for storing university-specific information and settings."""
    
    __tablename__ = 'university_info'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    university_name = db.Column(db.String(200), nullable=False)
    university_code = db.Column(db.String(10), unique=True, nullable=False)
    
    # Contact Information
    contact_email = db.Column(db.String(255))
    contact_phone = db.Column(db.String(20))
    website = db.Column(db.String(255))
    
    # Address
    address = db.Column(db.Text)
    
    # Chatbot Configuration
    welcome_message = db.Column(db.Text)
    system_prompt = db.Column(db.Text)
    
    # Application Configuration
    required_documents = db.Column(db.JSON)  # List of required documents for applications
    application_deadline = db.Column(db.Date)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

class ApplicantData(db.Model):
    __tablename__ = 'applicant_data'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(36), db.ForeignKey('chat_sessions.id'), nullable=False)
    name = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    intended_program = db.Column(db.String(255), nullable=True)
    application_status = db.Column(db.String(50), default='interested')
    data_collection_status = db.Column(db.String(50), default='collecting')  # collecting, complete
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    
    # Relationship
    session = db.relationship('ChatSession', backref='applicant_data')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'name': self.name,
            'phone': self.phone,
            'email': self.email,
            'intended_program': self.intended_program,
            'application_status': self.application_status,
            'data_collection_status': self.data_collection_status
        } 