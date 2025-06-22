from flask import request, jsonify
from app.admin import admin_bp
from app.models import Application, ChatSession
from app import db
import logging

@admin_bp.route('/applications', methods=['GET'])
def list_applications():
    """List all applications for university representatives."""
    try:
        applications = Application.query.order_by(Application.submitted_at.desc()).all()
        
        application_list = []
        for app in applications:
            application_list.append({
                'id': app.id,
                'first_name': app.first_name,
                'last_name': app.last_name,
                'email': app.email,
                'phone': app.phone,
                'program_interest': app.program_interest,
                'status': app.status.value if app.status else 'pending',
                'submitted_at': app.submitted_at.isoformat(),
                'updated_at': app.updated_at.isoformat()
            })
        
        return jsonify({
            'applications': application_list,
            'total_count': len(application_list)
        })
        
    except Exception as e:
        logging.error(f"Error listing applications: {str(e)}")
        return jsonify({'error': 'Failed to retrieve applications'}), 500

@admin_bp.route('/applications/<application_id>', methods=['GET'])
def get_application_details(application_id):
    """Get detailed information about a specific application."""
    try:
        application = Application.query.get(application_id)
        if not application:
            return jsonify({'error': 'Application not found'}), 404
        
        return jsonify({
            'id': application.id,
            'personal_info': {
                'first_name': application.first_name,
                'last_name': application.last_name,
                'email': application.email,
                'phone': application.phone,
                'date_of_birth': application.date_of_birth.isoformat() if application.date_of_birth else None
            },
            'address': {
                'address_line1': application.address_line1,
                'address_line2': application.address_line2,
                'city': application.city,
                'state': application.state,
                'postal_code': application.postal_code,
                'country': application.country
            },
            'academic_info': {
                'program_interest': application.program_interest,
                'previous_education': application.previous_education,
                'gpa': application.gpa,
                'test_scores': application.test_scores
            },
            'status': application.status.value if application.status else 'pending',
            'agent_notes': application.agent_notes,
            'missing_information': application.missing_information,
            'admin_notes': application.admin_notes,
            'reviewed_by': application.reviewed_by,
            'reviewed_at': application.reviewed_at.isoformat() if application.reviewed_at else None,
            'submitted_at': application.submitted_at.isoformat(),
            'updated_at': application.updated_at.isoformat()
        })
        
    except Exception as e:
        logging.error(f"Error getting application details: {str(e)}")
        return jsonify({'error': 'Failed to retrieve application details'}), 500 