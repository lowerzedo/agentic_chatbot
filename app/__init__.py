from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from config import config
import os
from flask_migrate import Migrate

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name=None):
    """Application factory pattern for creating Flask app instances."""
    
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV') or 'default'
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    
    # Register blueprints
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    from app.chat import chat_bp
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    
    from app.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    
    # Create upload directory if it doesn't exist
    upload_folder = app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Create vector database directory if it doesn't exist
    vector_db_path = app.config['VECTOR_DB_PATH']
    if not os.path.exists(vector_db_path):
        os.makedirs(vector_db_path)
    
    return app 