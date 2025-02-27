# parts/models.py

from django.db import models
from django.contrib.auth.models import User
import os
from django.urls import reverse

class Part(models.Model):
    """
    Model for parts with hierarchical relationship
    """
    # Basic part information
    part_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    level = models.IntegerField(default=0)  # Hierarchical level (0 = root, 1 = first level, etc.)
    info = models.TextField(blank=True, null=True)  # Additional information
    
    # Hierarchical relationship
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    # Audit fields
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_parts')
    created_at = models.DateTimeField(auto_now_add=True)
    modified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='modified_parts')
    modified_at = models.DateTimeField(auto_now=True)
    
    # Tracking
    is_active = models.BooleanField(default=True)
    
    # Add codification fields
    equipment_code = models.CharField(max_length=100, blank=True, null=True, help_text="Equipment codification code")
    codification_level = models.PositiveSmallIntegerField(default=0, help_text="Codification hierarchy level")
    system_code = models.CharField(max_length=20, blank=True, null=True, help_text="Level 1 system code")
    subsystem_code = models.CharField(max_length=20, blank=True, null=True, help_text="Level 2 subsystem code")
    component_code = models.CharField(max_length=20, blank=True, null=True, help_text="Level 3 component code")
    subcomponent_code = models.CharField(max_length=20, blank=True, null=True, help_text="Level 4 subcomponent code")
    
    class Meta:
        ordering = ['level', 'part_id']
    
    def __str__(self):
        return f"{self.part_id} - {self.name}"
    
    def get_absolute_url(self):
        return reverse('part-detail', kwargs={'pk': self.pk})
    
    def get_all_children(self):
        """Returns all children parts recursively"""
        children = list(self.children.all())
        for child in self.children.all():
            children.extend(child.get_all_children())
        return children
    
    @property
    def has_documents(self):
        return self.documents.exists()
    
    @property
    def primary_document(self):
        """Returns the first document if any exist"""
        return self.documents.first()
    
    def get_formatted_equipment_code(self):
        """Return the equipment code formatted with proper separators and HTML markup"""
        if not self.equipment_code:
            return ""
            
        parts = self.equipment_code.split('-')
        formatted_parts = []
        
        for i, part in enumerate(parts):
            level_class = f"code-level-{i+1}"
            formatted_parts.append(f'<span class="{level_class}">{part}</span>')
            
        return '-'.join(formatted_parts)

class Document(models.Model):
    """
    Model for documents associated with parts
    """
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    
    # Document type choices
    DOCUMENT_TYPE_CHOICES = (
        ('drawing', 'Technical Drawing'),
        ('manual', 'Manual'),
        ('datasheet', 'Datasheet'),
        ('schematic', 'Schematic'),
        ('photo', 'Photo'),
        ('other', 'Other'),
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES, default='other')
    
    # The document file
    file = models.FileField(upload_to='documents/')
    
    # Audit fields
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_documents')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} ({self.document_type}) - {self.part.part_id}"
    
    def get_absolute_url(self):
        return reverse('document-detail', kwargs={'pk': self.pk})
    
    @property
    def filename(self):
        return os.path.basename(self.file.name)
    
    @property
    def file_extension(self):
        return os.path.splitext(self.filename)[1].lower()
    
    @property
    def is_image(self):
        return self.file_extension in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
    
    @property
    def is_pdf(self):
        return self.file_extension == '.pdf'
    
    @property
    def is_text(self):
        return self.file_extension in ['.txt', '.csv', '.md']

class ImportLog(models.Model):
    """
    Track CSV imports for auditing
    """
    file_name = models.CharField(max_length=255)
    imported_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='imports')
    imported_at = models.DateTimeField(auto_now_add=True)
    parts_added = models.IntegerField(default=0)
    parts_updated = models.IntegerField(default=0)
    parts_skipped = models.IntegerField(default=0)
    log_message = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-imported_at']
    
    def __str__(self):
        return f"Import {self.file_name} by {self.imported_by} on {self.imported_at}"

class MarkedPart(models.Model):
    """
    Model to track marked parts per user
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='marked_parts')
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='marked_by')
    marked_at = models.DateTimeField(auto_now_add=True)
    note = models.TextField(blank=True, null=True)  # Optional note about why it was marked
    
    class Meta:
        unique_together = ['user', 'part']  # Each user can mark a part only once
        ordering = ['-marked_at']
    
    def __str__(self):
        return f"{self.user.username} marked {self.part.part_id}"