# users/forms.py

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import UserProfile

class UserRegisterForm(UserCreationForm):
    """Form for user registration"""
    email = forms.EmailField()
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

class UserLoginForm(AuthenticationForm):
    """Custom login form with bootstrap styling"""
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class UserUpdateForm(forms.ModelForm):
    """Form for updating user information"""
    email = forms.EmailField()
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']

class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    class Meta:
        model = UserProfile
        fields = ['role', 'show_parts_tree_expanded']
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'show_parts_tree_expanded': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AdminUserProfileForm(forms.ModelForm):
    """Form for administrators to update user profiles including permissions"""
    class Meta:
        model = UserProfile
        fields = [
            'role', 
            'can_add_parts', 
            'can_edit_parts', 
            'can_delete_parts', 
            'can_view_documents', 
            'can_add_documents', 
            'can_upload_csv'
        ]
        widgets = {
            'role': forms.Select(attrs={'class': 'form-control'}),
            'can_add_parts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_edit_parts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_delete_parts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_documents': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_add_documents': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_upload_csv': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }