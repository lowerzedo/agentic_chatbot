from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    # Check if table exists
    result = db.session.execute(text("SELECT tablename FROM pg_tables WHERE tablename = 'applicant_data'"))
    if result.fetchone():
        print(" applicant_data table exists!")
        
        # Show table structure
        result = db.session.execute(text("""
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'applicant_data'
        """))
        
        print("\nTable structure:")
        for row in result:
            print(f"  {row[0]}: {row[1]} ({'NULL' if row[2] == 'YES' else 'NOT NULL'})")
    else:
        print(" applicant_data table not found") 