# users/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class UserProfile(models.Model):
    """
    Extended user profile with additional permissions and preferences
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # User role choices
    ROLE_CHOICES = (
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('engineer', 'Engineer'),
        ('technician', 'Technician'),
        ('viewer', 'Viewer'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='viewer')
    
    # Permissions
    can_add_parts = models.BooleanField(default=False)
    can_edit_parts = models.BooleanField(default=False)
    can_delete_parts = models.BooleanField(default=False)
    can_view_documents = models.BooleanField(default=True)
    can_add_documents = models.BooleanField(default=False)
    can_upload_csv = models.BooleanField(default=False)
    
    # User preferences
    show_parts_tree_expanded = models.BooleanField(default=False)
    
    # Audit fields
    date_joined = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile ({self.role})"
    
    def save(self, *args, **kwargs):
        """Set permissions based on role automatically"""
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
            self.can_edit_parts = True
            self.can_delete_parts = False
            self.can_view_documents = True
            self.can_add_documents = False
            self.can_upload_csv = False
        # Viewer role has default permissions (can only view parts)
            
        super().save(*args, **kwargs)

class UserActivity(models.Model):
    """
    Track user activity in the system for auditing
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50)  # e.g., 'login', 'add_part', 'edit_part', etc.
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'User Activities'
        ordering = ['-timestamp']
    
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
    instance.profile.save()