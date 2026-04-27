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
UNIT_LOGO_PREFIX = 'unit_logos/'


def _strip_upload_url_prefix(path):
    if path.startswith('/api/uploads/'):
        return path[len('/api/uploads/'):]
    if path.startswith('/uploads/'):
        return path[len('/uploads/'):]
    if path.startswith('/'):
        return path[1:]
    return path


def normalize_logo_reference(value):
    """
    Normalize a local logo reference into a storage key format.

    Examples:
    - /api/uploads/unit_logos/file.png -> unit_logos/file.png
    - https://cdn.example.com/unit_logos/file.png -> unit_logos/file.png
    - file.png -> unit_logos/file.png
    """
    if not value:
        return None

    raw = str(value).strip()
    if not raw:
        return None

    parsed_path = urlparse(raw).path if '://' in raw else raw
    if not parsed_path:
        return None

    normalized_path = _strip_upload_url_prefix(parsed_path.strip())
    normalized_path = normalized_path.replace('\\', '/').strip('/')
    if not normalized_path:
        return None

    if normalized_path.startswith(UNIT_LOGO_PREFIX):
        return normalized_path

    if '/unit_logos/' in normalized_path:
        tail = normalized_path.split('/unit_logos/', 1)[1].strip('/')
        return f"{UNIT_LOGO_PREFIX}{tail}" if tail else None

    filename = os.path.basename(normalized_path)
    if not filename:
        return None
    return f"{UNIT_LOGO_PREFIX}{filename}"


def get_logo_storage_key(filename):
    """Build storage key for a local unit logo filename."""
    if not filename:
        return None
    safe_name = secure_filename(str(filename))
    if not safe_name:
        return None
    return f"{UNIT_LOGO_PREFIX}{safe_name}"


def is_local_logo_reference(value):
    """Return True when value points to the app local upload namespace."""
    reference = normalize_logo_reference(value)
    return bool(reference and reference.startswith(UNIT_LOGO_PREFIX))


def prepare_logo_storage_value(value):
    """
    Normalize logo value before persisting in DB.

    - Local references are stored as unit_logos/<filename>
    - External absolute URLs are preserved as-is
    """
    if not value:
        return None

    raw = str(value).strip()
    if not raw:
        return None

    if raw.startswith('http://') or raw.startswith('https://'):
        if is_local_logo_reference(raw):
            return normalize_logo_reference(raw)
        return raw

    normalized_reference = normalize_logo_reference(raw)
    return normalized_reference or raw


def get_unit_logo_folder_candidates(include_legacy_fallback=False):
    """Return configured and optional legacy unit logo folders (without duplicates)."""
    configured = os.path.abspath(current_app.config['UNIT_LOGO_FOLDER'])
    candidates = [configured]

    if include_legacy_fallback and current_app.config.get('ENABLE_LEGACY_UPLOAD_FALLBACK', True):
        fallback = os.path.abspath(os.path.join(current_app.root_path, '..', 'uploads', 'unit_logos'))
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
        upload_folder = get_unit_logo_folder_candidates(include_legacy_fallback=False)[0]
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, unique_filename)
        file.stream.seek(0)
        file.save(file_path)
        logger.info(f"Logo saved successfully: {unique_filename} (folder: {upload_folder})")
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
        storage_key = normalize_logo_reference(filename)
        if not storage_key:
            return True

        parsed_filename = extract_logo_filename(storage_key)
        if not parsed_filename:
            return True
        
        deleted_any = False
        for upload_folder in get_unit_logo_folder_candidates(include_legacy_fallback=True):
            file_path = os.path.join(upload_folder, parsed_filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                deleted_any = True
                logger.info(f"Logo deleted: {parsed_filename} (folder: {upload_folder})")

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


def resolve_logo_public_url(logo_reference):
    """
    Resolve a stored logo reference or legacy URL into a public URL.
    """
    if not logo_reference:
        return None

    raw_value = str(logo_reference).strip()
    if not raw_value:
        return None

    if raw_value.startswith('http://') or raw_value.startswith('https://'):
        if is_local_logo_reference(raw_value):
            pass
        else:
            return raw_value

    normalized_reference = normalize_logo_reference(raw_value)
    if not normalized_reference:
        return raw_value

    filename = extract_logo_filename(normalized_reference)
    if not filename:
        return raw_value

    base_url = get_upload_base_url()
    if base_url:
        return f"{base_url}/unit_logos/{filename}"
    return f"/api/uploads/unit_logos/{filename}"


def get_logo_url(filename):
    """Backward-compatible alias: resolve a public URL from filename/reference."""
    return resolve_logo_public_url(filename)

def is_logo_url_local(logo_url):
    """
    Check if a logo URL is served by this app's upload configuration.
    """
    return is_local_logo_reference(logo_url)

def extract_logo_filename(logo_url):
    """
    Extract the filename from a logo URL or path.
    """
    normalized_reference = normalize_logo_reference(logo_url)
    if not normalized_reference:
        return None

    parsed_path = normalized_reference
    if not parsed_path:
        return None

    parts = parsed_path.rstrip('/').split('/')
    return parts[-1] if parts else None
