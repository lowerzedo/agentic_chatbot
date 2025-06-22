import os
from app import create_app, db
from app.models import ChatSession, ChatMessage, Application, Document, UniversityInfo

# Create Flask application
app = create_app(os.getenv('FLASK_ENV') or 'default')

@app.shell_context_processor
def make_shell_context():
    """Make database models available in Flask shell."""
    return {
        'db': db,
        'ChatSession': ChatSession,
        'ChatMessage': ChatMessage,
        'Application': Application,
        'Document': Document,
        'UniversityInfo': UniversityInfo
    }

@app.cli.command()
def init_db():
    """Initialize the database."""
    db.create_all()
    print("Database tables created.")

@app.cli.command()
def setup_university():
    """Setup basic university information."""
    university = UniversityInfo.query.first()
    if not university:
        university = UniversityInfo(
            university_name="Sample University",
            university_code="SU",
            contact_email="admissions@sampleuni.edu",
            contact_phone="+1-555-123-4567",
            website="https://www.sampleuni.edu",
            address="123 University Ave, College Town, ST 12345",
            welcome_message="Welcome to Sample University! I'm here to help you learn about our programs, admissions process, and campus life. How can I assist you today?",
            system_prompt="You are a helpful university chatbot assistant.",
            required_documents=["transcript", "personal_statement", "letters_of_recommendation"]
        )
        db.session.add(university)
        db.session.commit()
        print("University information created.")
    else:
        print("University information already exists.")

if __name__ == '__main__':
    app.run(debug=True) 