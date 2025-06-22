#!/usr/bin/env python3
"""
Setup script for University Chatbot Backend
This script helps initialize the application for development and testing.
"""

import os
import sys
from app import create_app, db
from app.models import UniversityInfo

def create_env_file():
    """Create a basic .env file with placeholders."""
    env_content = """# Database Configuration
SUPABASE_URL=your_supabase_project_url_here
SUPABASE_KEY=your_supabase_anon_key_here
DATABASE_URL=sqlite:///university_chatbot.db

# Google AI Configuration
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-for-development

# Application Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
VECTOR_DB_PATH=./vector_db
"""
    
    if not os.path.exists('.env'):
        with open('.env', 'w') as f:
            f.write(env_content)
        print("✅ Created .env file with placeholders")
        print("⚠️  Please update the .env file with your actual API keys")
    else:
        print(".env file already exists")

def setup_directories():
    """Create necessary directories."""
    directories = ['uploads', 'vector_db', 'logs']
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

def initialize_database():
    """Initialize the database with tables."""
    try:
        app = create_app('development')
        with app.app_context():
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Create sample university info if it doesn't exist
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
                print("✅ Sample university information created")
            else:
                print("University information already exists")
                
    except Exception as e:
        print(f"❌ Error initializing database: {str(e)}")
        return False
    
    return True

def main():
    """Main setup function."""
    print("🏫 University Chatbot Backend Setup")
    print("=" * 40)
    
    # Create environment file
    create_env_file()
    
    # Setup directories
    setup_directories()
    
    # Initialize database
    if initialize_database():
        print("\n✅ Setup completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Update your .env file with actual API keys")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Run the application: python app.py")
        print("4. Upload some PDF documents via the API")
        print("5. Start testing the chatbot!")
    else:
        print("\n❌ Setup failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 