# users/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView

from .forms import UserRegisterForm, UserLoginForm, UserUpdateForm, ProfileUpdateForm, AdminUserProfileForm
from .models import UserProfile, UserActivity

class CustomLoginView(LoginView):
    """Custom login view with better styling"""
    form_class = UserLoginForm
    template_name = 'users/login.html'
    
    def form_valid(self, form):
        # Log the login activity
        response = super().form_valid(form)
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='login',
            description=f'User logged in from {self.request.META.get("REMOTE_ADDR")}',
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        return response

class RegisterView(CreateView):
    """User registration view"""
    form_class = UserRegisterForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Your account has been created! You can now log in.')
        return response

@login_required
def profile(request):
    """View and update user profile"""
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            # Log the profile update
            UserActivity.objects.create(
                user=request.user,
                activity_type='profile_update',
                description='User updated their profile',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_activities': UserActivity.objects.filter(user=request.user).order_by('-timestamp')[:10]
    }
    
    return render(request, 'users/profile.html', context)

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == 'admin'

@login_required
@user_passes_test(is_admin)
def user_list(request):
    """View all users (admin only)"""
    users = User.objects.all().order_by('username')
    return render(request, 'users/user_list.html', {'users': users})

@login_required
@user_passes_test(is_admin)
def user_detail(request, pk):
    """View user details (admin only)"""
    user = get_object_or_404(User, pk=pk)
    activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:20]
    
    return render(request, 'users/user_detail.html', {
        'user_obj': user,
        'activities': activities
    })

@login_required
@user_passes_test(is_admin)
def edit_user_profile(request, pk):
    """Edit user profile (admin only)"""
    user = get_object_or_404(User, pk=pk)
    profile = user.profile
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=user)
        profile_form = AdminUserProfileForm(request.POST, instance=profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            # Log the admin update
            UserActivity.objects.create(
                user=request.user,
                activity_type='admin_profile_update',
                description=f'Admin updated profile for user {user.username}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'Profile for {user.username} has been updated!')
            return redirect('user-detail', pk=user.pk)
    else:
        user_form = UserUpdateForm(instance=user)
        profile_form = AdminUserProfileForm(instance=profile)
    
    return render(request, 'users/edit_user_profile.html', {
        'user_obj': user,
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def activity_log(request):
    """View your own activity log"""
    activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'users/activity_log.html', {'activities': activities})

@login_required
@user_passes_test(is_admin)
def all_activity_log(request):
    """View all user activities (admin only)"""
    activities = UserActivity.objects.all().order_by('-timestamp')
    return render(request, 'users/all_activity_log.html', {'activities': activities})