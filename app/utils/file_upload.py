"""
Helper functions for file uploads
"""
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
import logging

logger = logging.getLogger(__name__)

def allowed_file(filename, allowed_extensions):
    """
    Check if a file has an allowed extension.
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_logo(file, unit_id):
    """
    Save a logo file for a unit.
    
    Args:
        file: FileStorage object from Flask request
        unit_id: ID of the unit
    
    Returns:
        tuple: (success: bool, filename: str or error_message: str)
    """
    try:
        # Check if file is provided
        if not file or file.filename == '':
            return False, "No file provided"
        
        # Check if file type is allowed
        if not allowed_file(file.filename, current_app.config['ALLOWED_LOGO_EXTENSIONS']):
            allowed = ', '.join(current_app.config['ALLOWED_LOGO_EXTENSIONS'])
            return False, f"Invalid file type. Allowed types: {allowed}"
        
        # Create upload folder if it doesn't exist
        upload_folder = current_app.config['UNIT_LOGO_FOLDER']
        os.makedirs(upload_folder, exist_ok=True)
        
        # Generate unique filename
        file_extension = secure_filename(file.filename).rsplit('.', 1)[1].lower()
        unique_filename = f"unit_{unit_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        file_path = os.path.join(upload_folder, unique_filename)
        
        # Save file
        file.save(file_path)
        
        logger.info(f"Logo saved successfully: {unique_filename}")
        return True, unique_filename
    
    except Exception as e:
        logger.error(f"Error saving logo: {e}")
        return False, str(e)

def delete_logo(filename):
    """
    Delete a logo file.
    
    Args:
        filename: Name of the file to delete
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not filename:
            return True
        
        file_path = os.path.join(current_app.config['UNIT_LOGO_FOLDER'], filename)
        
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Logo deleted: {filename}")
            return True
        
        return True  # File doesn't exist, consider it "deleted"
    
    except Exception as e:
        logger.error(f"Error deleting logo: {e}")
        return False

def get_logo_url(filename):
    """
    Generate URL for accessing a logo file.
    
    Args:
        filename: Name of the logo file
    
    Returns:
        str: URL to access the file
    """
    if not filename:
        return None
    return f"/api/uploads/unit_logos/{filename}"
