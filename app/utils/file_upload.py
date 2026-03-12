"""
Helper functions for file uploads
"""
import os
import uuid
from urllib.parse import urlparse
from werkzeug.utils import secure_filename
from flask import current_app
import logging

logger = logging.getLogger(__name__)


def get_unit_logo_folder_candidates():
    """Return configured and fallback unit logo folders (without duplicates)."""
    configured = os.path.abspath(current_app.config['UNIT_LOGO_FOLDER'])
    fallback = os.path.abspath(os.path.join(current_app.root_path, '..', 'uploads', 'unit_logos'))

    candidates = [configured]
    if os.path.normcase(fallback) != os.path.normcase(configured):
        candidates.append(fallback)
    return candidates

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
        
        # Generate unique filename
        file_extension = secure_filename(file.filename).rsplit('.', 1)[1].lower()
        unique_filename = f"unit_{unit_id}_{uuid.uuid4().hex[:8]}.{file_extension}"
        save_errors = []

        for upload_folder in get_unit_logo_folder_candidates():
            try:
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, unique_filename)
                file.stream.seek(0)
                file.save(file_path)
                logger.info(f"Logo saved successfully: {unique_filename} (folder: {upload_folder})")
                return True, unique_filename
            except Exception as save_error:
                save_errors.append(f"{upload_folder}: {save_error}")

        logger.error("Error saving logo in all candidate folders: %s", " | ".join(save_errors))
        return False, "Could not save logo file in configured upload locations"
    
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
        
        deleted_any = False
        for upload_folder in get_unit_logo_folder_candidates():
            file_path = os.path.join(upload_folder, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_any = True
                logger.info(f"Logo deleted: {filename} (folder: {upload_folder})")

        if deleted_any:
            return True
        
        return True  # File doesn't exist, consider it "deleted"
    
    except Exception as e:
        logger.error(f"Error deleting logo: {e}")
        return False

def get_upload_base_url():
    """
    Get the public base URL for uploads if configured.
    """
    base_url = current_app.config.get('UPLOAD_PUBLIC_BASE_URL')
    return base_url.rstrip('/') if base_url else None

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
    base_url = get_upload_base_url()
    if base_url:
        return f"{base_url}/unit_logos/{filename}"
    return f"/api/uploads/unit_logos/{filename}"

def is_logo_url_local(logo_url):
    """
    Check if a logo URL is served by this app's upload configuration.
    """
    if not logo_url:
        return False
    if logo_url.startswith('/api/uploads/'):
        return True
    base_url = get_upload_base_url()
    if base_url and logo_url.startswith(f"{base_url}/"):
        return True
    return False

def extract_logo_filename(logo_url):
    """
    Extract the filename from a logo URL or path.
    """
    if not logo_url:
        return None
    parsed_path = urlparse(logo_url).path if '://' in logo_url else logo_url
    if not parsed_path:
        return None
    parts = parsed_path.rstrip('/').split('/')
    return parts[-1] if parts else None
