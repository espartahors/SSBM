# users/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    """Extended user profile with role and permissions"""
    
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('engineer', 'Engineer'),
        ('technician', 'Technician'),
        ('viewer', 'Viewer'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    
    # UI preferences
    show_parts_tree_expanded = models.BooleanField(default=False)
    
    # Permissions
    can_add_parts = models.BooleanField(default=False)
    can_edit_parts = models.BooleanField(default=False)
    can_delete_parts = models.BooleanField(default=False)
    can_view_documents = models.BooleanField(default=True)
    can_add_documents = models.BooleanField(default=False)
    can_upload_csv = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"
    
    def save(self, *args, **kwargs):
        """
        Override save to set default permissions based on role
        """
        # Set default permissions based on role
        if self.role == 'admin':
            self.can_add_parts = True
            self.can_edit_parts = True
            self.can_delete_parts = True
            self.can_view_documents = True
            self.can_add_documents = True
            self.can_upload_csv = True
        elif self.role == 'manager':
            self.can_add_parts = True
            self.can_edit_parts = True
            self.can_delete_parts = False
            self.can_view_documents = True
            self.can_add_documents = True
            self.can_upload_csv = True
        elif self.role == 'engineer':
            self.can_add_parts = True
            self.can_edit_parts = True
            self.can_delete_parts = False
            self.can_view_documents = True
            self.can_add_documents = True
            self.can_upload_csv = False
        elif self.role == 'technician':
            self.can_add_parts = False
            self.can_edit_parts = False
            self.can_delete_parts = False
            self.can_view_documents = True
            self.can_add_documents = False
            self.can_upload_csv = False
        elif self.role == 'viewer':
            self.can_add_parts = False
            self.can_edit_parts = False
            self.can_delete_parts = False
            self.can_view_documents = True
            self.can_add_documents = False
            self.can_upload_csv = False
            
        super().save(*args, **kwargs)

class UserActivity(models.Model):
    """Model to track user activities for audit purposes"""
    
    ACTIVITY_TYPES = (
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('profile_update', 'Profile Update'),
        ('admin_profile_update', 'Admin Updated Profile'),
        ('part_create', 'Created Part'),
        ('part_update', 'Updated Part'),
        ('part_delete', 'Deleted Part'),
        ('part_mark', 'Marked Part'),
        ('part_unmark', 'Unmarked Part'),
        ('clear_all_marks', 'Cleared All Marks'),
        ('document_upload', 'Uploaded Document'),
        ('document_update', 'Updated Document'),
        ('document_delete', 'Deleted Document'),
        ('csv_import', 'Imported CSV'),
        ('csv_export', 'Exported CSV'),
        ('equipment_create', 'Created Equipment'),
        ('equipment_update', 'Updated Equipment'),
        ('equipment_delete', 'Deleted Equipment'),
        ('equipment_position_update', 'Updated Equipment Position'),
        ('equipment_csv_import', 'Imported Equipment CSV'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    timestamp = models.DateTimeField(auto_now_add=True)
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = 'User Activities'
    
    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.timestamp}"

# Signal to create user profile when a new user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# Signal to save user profile when user is saved
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if not hasattr(instance, 'profile'):
        UserProfile.objects.create(user=instance)
    instance.profile.save()