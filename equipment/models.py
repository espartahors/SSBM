# equipment/models.py
from django.db import models
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
from parts.models import Part

class EquipmentCategory(MPTTModel):
    """Equipment category for organizing equipment in a hierarchy"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    class MPTTMeta:
        order_insertion_by = ['name']
    
    def __str__(self):
        return self.name

# equipment/models.py
from django.db import models
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey

class Equipment(models.Model):
    """Equipment item model with hierarchical structure"""
    # Basic information
    code = models.CharField(max_length=50, help_text="Equipment code (without parent prefix)")
    full_code = models.CharField(max_length=150, blank=True, help_text="Full hierarchical code including parent codes")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    level = models.PositiveIntegerField(default=1, help_text="Hierarchy level (1=root, 2=child, etc.)")
    
    # Relationships
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                              related_name='children')
    
    # Additional metadata
    fabricant = models.CharField(max_length=100, blank=True, help_text="Manufacturer/brand")
    doc_reference = models.CharField(max_length=100, blank=True, help_text="Reference documentation")
    
    # Status and organization
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Under Maintenance'),
        ('decommissioned', 'Decommissioned'),
    ], default='active')
    position = models.PositiveIntegerField(default=0, help_text="Display order within same level")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['level', 'position', 'code']
        unique_together = [['parent', 'code']]  # Prevent duplicate codes under same parent
    
    def __str__(self):
        return f"{self.full_code} - {self.name}"
    
    def save(self, *args, **kwargs):
        # Generate the full_code based on parent hierarchy
        if self.parent:
            self.full_code = f"{self.parent.full_code}-{self.code}"
        else:
            self.full_code = self.code
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('equipment-detail', kwargs={'pk': self.pk})