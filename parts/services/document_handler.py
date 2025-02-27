# parts/services/document_handler.py

import os
import mimetypes
import logging
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from parts.models import Document

logger = logging.getLogger(__name__)

class DocumentHandler:
    """Service class for handling documents"""
    
    # Define allowed file extensions
    ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg']
    ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.txt', '.csv', '.md', '.docx', '.xlsx', '.dwg', '.dxf']
    
    @classmethod
    def get_allowed_extensions(cls):
        """Return all allowed file extensions"""
        return cls.ALLOWED_IMAGE_EXTENSIONS + cls.ALLOWED_DOCUMENT_EXTENSIONS
    
    @classmethod
    def validate_file(cls, file):
        """
        Validate a file:
        - Check extension is allowed
        - Validate file size
        - Basic content validation
        """
        # Get file extension
        filename = file.name
        ext = os.path.splitext(filename)[1].lower()
        
        # Check extension
        if ext not in cls.get_allowed_extensions():
            raise ValidationError(f"File type not allowed. Allowed types: {', '.join(cls.get_allowed_extensions())}")
        
        # Check file size (limit to 20MB)
        if file.size > 20 * 1024 * 1024:  # 20MB in bytes
            raise ValidationError("File size too large. Maximum size is 20MB.")
        
        # For more security, we could implement additional content validation here
        
        return True
    
    @classmethod
    def detect_document_type(cls, file):
        """Try to detect appropriate document type based on file extension"""
        filename = file.name
        ext = os.path.splitext(filename)[1].lower()
        
        # Map extensions to document types
        type_map = {
            '.pdf': 'manual' if 'manual' in filename.lower() else 'datasheet',
            '.dwg': 'drawing',
            '.dxf': 'drawing',
            '.jpg': 'photo',
            '.jpeg': 'photo', 
            '.png': 'photo',
            '.gif': 'photo',
            '.svg': 'schematic',
        }
        
        return type_map.get(ext, 'other')
    
    @classmethod
    def save_uploaded_file(cls, uploaded_file, target_path=None):
        """
        Save an uploaded file to the storage system
        If target_path is None, use the uploaded file name
        """
        if target_path is None:
            target_path = f"documents/{uploaded_file.name}"
        
        # Ensure the file doesn't overwrite an existing file with the same name
        if default_storage.exists(target_path):
            base, ext = os.path.splitext(target_path)
            counter = 1
            while default_storage.exists(f"{base}_{counter}{ext}"):
                counter += 1
            target_path = f"{base}_{counter}{ext}"
        
        # Save the file
        path = default_storage.save(target_path, ContentFile(uploaded_file.read()))
        return path
    
    @classmethod
    def get_file_mime_type(cls, document):
        """Get MIME type for a document file"""
        file_path = document.file.path
        mime_type, encoding = mimetypes.guess_type(file_path)
        return mime_type or 'application/octet-stream'
    
    @classmethod
    def is_viewable_in_browser(cls, document):
        """Check if the document can be viewed directly in a browser"""
        ext = document.file_extension
        
        # Images, PDFs, and text files can be viewed in browser
        return (ext in cls.ALLOWED_IMAGE_EXTENSIONS or 
                ext == '.pdf' or 
                ext in ['.txt', '.csv', '.md'])
    
    @classmethod
    def get_file_content(cls, document):
        """
        Get file content as text if it's a text file
        Returns None if not a text file
        """
        if document.file_extension in ['.txt', '.csv', '.md']:
            try:
                with document.file.open('r') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"Error reading file {document.file.name}: {str(e)}")
                return None
        return None
    
    @classmethod
    def delete_document_file(cls, document):
        """Delete the file associated with a document"""
        try:
            if document.file and default_storage.exists(document.file.name):
                default_storage.delete(document.file.name)
                return True
        except Exception as e:
            logger.error(f"Error deleting file {document.file.name}: {str(e)}")
            return False
        return False