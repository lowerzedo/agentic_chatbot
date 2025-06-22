# University Chatbot Backend

A comprehensive backend system for university chatbots featuring RAG (Retrieval-Augmented Generation) capabilities and agentic application processing using Google Gemini AI.

## Features

### Core Functionality

- **RAG-based Chatbot**: Process university PDF documents and provide intelligent responses
- **Google Gemini Integration**: Advanced natural language processing and generation
- **Chat Session Management**: Persistent conversation sessions with history
- **Document Processing**: Upload and process PDF documents for knowledge base
- **Vector Database**: ChromaDB for efficient document retrieval
- **Application Intent Detection**: AI-powered detection of enrollment applications

### Agentic Capabilities (Planned)

- **Google Agent SDK Integration**: Intelligent application processing agents
- **Application Data Collection**: Automated gathering of student information
- **Admin Dashboard**: University representatives can review applications
- **Status Management**: Track application progress and status

### Technical Stack

- **Backend**: Flask with SQLAlchemy
- **Database**: PostgreSQL (Supabase) with SQLite fallback
- **AI/ML**: Google Gemini API, Sentence Transformers
- **Vector Database**: ChromaDB
- **Deployment**: AWS Lambda ready (with Mangum)

## Project Structure

```
agentic_chatbot/
├── app/
│   ├── __init__.py              # Flask application factory
│   ├── models.py                # Database models
│   ├── api/                     # Main API endpoints
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── chat/                    # Chat functionality
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── admin/                   # Admin endpoints
│   │   ├── __init__.py
│   │   └── routes.py
│   └── services/                # Business logic services
│       ├── __init__.py
│       ├── gemini_service.py    # Google Gemini integration
│       └── rag_service.py       # RAG processing
├── config.py                    # Configuration management
├── app.py                       # Main application entry point
├── requirements.txt             # Python dependencies
├── setup.py                     # Setup and initialization script
├── test_api.py                  # API testing script
└── README.md                    # This file
```

## Quick Start

### 1. Initial Setup

```bash
# Clone the repository
git clone <your-repo>
cd agentic_chatbot

# Install dependencies
pip install -r requirements.txt

# Run setup script
python setup.py
```

### 2. Configure Environment

Update the `.env` file with your API keys:

```env
# Google AI Configuration
GOOGLE_API_KEY=your_actual_google_gemini_api_key

# Database Configuration (for production)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# For development, SQLite is used by default
DATABASE_URL=sqlite:///university_chatbot.db
```

### 3. Run the Application

```bash
# Development mode
python app.py

# Or using Flask CLI
flask run
```

### 4. Test the API

```bash
# Run automated tests
python test_api.py
```

## API Endpoints

### General Endpoints

- `GET /api/health` - Health check
- `GET /api/university-info` - Get university information
- `GET /api/documents` - List uploaded documents
- `POST /api/upload-document` - Upload PDF document
- `DELETE /api/documents/<id>` - Delete document
- `GET /api/vector-stats` - Vector database statistics

### Chat Endpoints

- `POST /api/chat/session` - Create new chat session
- `POST /api/chat/session/<id>/message` - Send message
- `GET /api/chat/session/<id>/messages` - Get chat history

### Admin Endpoints

- `GET /api/admin/applications` - List applications
- `GET /api/admin/applications/<id>` - Get application details

## Usage Examples

### 1. Create Chat Session

```bash
curl -X POST http://localhost:5000/api/chat/session \
  -H "Content-Type: application/json"
```

Response:

```json
{
  "session_id": "uuid-here",
  "message": "Chat session created successfully",
  "welcome_message": "Welcome to Sample University! How can I help you today?"
}
```

### 2. Send Message

```bash
curl -X POST http://localhost:5000/api/chat/session/{session_id}/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What programs do you offer?"}'
```

### 3. Upload Document

```bash
curl -X POST http://localhost:5000/api/upload-document \
  -F "file=@university_handbook.pdf" \
  -F "title=University Handbook" \
  -F "category=general"
```

## Database Models

### Core Models

- **ChatSession**: Manages chat sessions
- **ChatMessage**: Individual messages with RAG metadata
- **UniversityInfo**: University configuration and settings
- **Document**: PDF documents for RAG processing
- **Application**: Student application data (for agentic processing)

### Key Features

- UUID primary keys for security
- JSON fields for flexible metadata storage
- Automatic timestamp management
- Proper foreign key relationships

## Development Workflow

### Phase 1: Basic RAG Chatbot ✅

1. ✅ Project structure and configuration
2. ✅ Database models and Flask setup
3. ✅ Google Gemini integration
4. ✅ RAG service with ChromaDB
5. ✅ Basic chat functionality
6. ✅ Document upload and processing

### Phase 2: Enhanced Features (Next)

1. 🔄 Application intent detection refinement
2. 🔄 Google Agent SDK integration
3. 🔄 Advanced application processing
4. 🔄 Admin dashboard enhancements

### Phase 3: Production Deployment

1. ⏳ AWS Lambda deployment configuration
2. ⏳ Supabase production database setup
3. ⏳ Error handling and logging improvements
4. ⏳ Performance optimization

## Testing

### Automated Testing

```bash
# Run API tests
python test_api.py

# Test specific endpoints
curl http://localhost:5000/api/health
```

### Manual Testing Workflow

1. Start the application
2. Upload a university PDF document
3. Create a chat session
4. Ask questions about the university
5. Test application intent ("I want to apply")

## Configuration

### Environment Variables

- `GOOGLE_API_KEY`: Required for Gemini AI
- `DATABASE_URL`: Database connection string
- `FLASK_ENV`: development/production
- `SECRET_KEY`: Flask session security
- `UPLOAD_FOLDER`: File upload directory
- `VECTOR_DB_PATH`: ChromaDB storage path

### Application Settings

- `CHUNK_SIZE`: Document chunking size (default: 1000)
- `CHUNK_OVERLAP`: Chunk overlap (default: 200)
- `TOP_K_RESULTS`: RAG retrieval results (default: 5)
- `MAX_CONVERSATION_HISTORY`: Chat history limit (default: 10)

## Deployment

### AWS Lambda (Planned)

```python
# lambda_handler.py
from mangum import Mangum
from app import create_app

app = create_app('production')
handler = Mangum(app)
```

### Docker (Optional)

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

## Security Considerations

- Environment variables for sensitive data
- Input validation and sanitization
- File upload restrictions (PDF only)
- Session management with secure UUIDs
- CORS configuration for frontend integration

## Contributing

1. Follow the modular architecture pattern
2. Add proper error handling and logging
3. Include tests for new features
4. Update documentation for API changes
5. Follow clean code principles

## Troubleshooting

### Common Issues

1. **Gemini API Key Error**

   - Ensure `GOOGLE_API_KEY` is set in `.env`
   - Verify the API key is valid and has proper permissions

2. **Database Connection Error**

   - Check `DATABASE_URL` configuration
   - For development, SQLite should work without additional setup

3. **Vector Database Issues**

   - Ensure `vector_db` directory exists and is writable
   - Check ChromaDB dependencies are installed

4. **File Upload Errors**
   - Verify `uploads` directory exists
   - Check file size limits in configuration

## License

[Your License Here]

## Support

For questions and support, please [create an issue] or contact the development team.
