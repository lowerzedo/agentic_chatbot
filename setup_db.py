#!/usr/bin/env python3
"""
Simple database setup script for ApplicantData table.
"""

from app import create_app, db

def setup_database():
    """Create all database tables."""
    app = create_app()
    
    with app.app_context():
        try:
            print(" Setting up database tables...")
            db.create_all()
            print(" Database setup complete!")
            
        except Exception as e:
            print(f" Database setup failed: {str(e)}")

if __name__ == "__main__":
    setup_database() 