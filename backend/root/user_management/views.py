# backend/root/user_management/views.py
"""
User Management Views for UPlant

This module contains Django class-based views for handling user-related operations
through traditional Django templates (not API endpoints). These views manage:
1. User registration/creation
2. Password changes
3. User profile updates

These template-based views complement the API endpoints defined in api/views.py
and are primarily used for the web interface.
"""

from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from user_management.forms import CustomUserCreationForm, CustomPasswordChangeForm
from user_management.models import User
from django.db.models import Q
from django.contrib import messages

class UserCreateView(CreateView):
    """
    Handles new user registration through web forms.
    
    This view processes the user registration form, creates new user accounts,
    and redirects users to the login page upon successful account creation.
    
    Attributes:
        model: The User model to create instances of
        form_class: The form used for user creation with validation logic
        template_name: The template that renders the registration form
        success_url: Where to redirect after successful registration
    """
    model = User
    form_class = CustomUserCreationForm
    template_name = 'user_management/create_user.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        """
        Process the valid form submission to create a new user.
        
        This method is called when valid form data has been POSTed.
        It creates the User object and displays a success message.
        
        Args:
            form: The validated form instance containing user data
            
        Returns:
            HttpResponse: Redirects to login page with success message
        """
        # Add debugging
        print("Form is valid!")
        response = super().form_valid(form)  # This saves the user object to the database
        messages.success(self.request, "Your account has been created successfully!")
        return response
    
    def form_invalid(self, form):
        """
        Handle the case when form validation fails.
        
        This method is called when invalid form data has been POSTed.
        It logs validation errors and returns the form with error messages.
        
        Args:
            form: The form instance with validation errors
            
        Returns:
            HttpResponse: Renders the same page but with error messages
        """
        # Add debugging
        print("Form is invalid!")
        print(form.errors)  # Logs the specific validation errors
        return super().form_invalid(form)
    
class PasswordChangeView(LoginRequiredMixin, UpdateView):
    """
    Handles password changes for authenticated users.
    
    This view allows logged-in users to change their password by providing
    their current password and a new password. It includes validation to ensure
    the current password is correct before making changes.
    
    Attributes:
        model: The User model to update
        form_class: The form used for password changing with validation
        template_name: The template that renders the password change form
        success_url: Where to redirect after successful password change
        
    Note:
        LoginRequiredMixin ensures only authenticated users can access this view
    """
    model = User
    form_class = CustomPasswordChangeForm
    template_name = 'user_management/change_password.html'
    success_url = reverse_lazy('core:login')

    def get_object(self, queryset=None):
        """
        Retrieve the User object to update.
        
        Instead of using a primary key from the URL, this method
        returns the currently authenticated user from the request.
        
        Args:
            queryset: Optional queryset to use (not used in this implementation)
            
        Returns:
            User: The currently authenticated user object
        """
        return self.request.user

    def form_valid(self, form):
        """
        Process the valid password change form.
        
        This method verifies that the old password is correct before
        setting and saving the new password.
        
        Security Note:
            We explicitly verify the old password as an additional security measure,
            even though the form should have already validated this.
        
        Args:
            form: The validated form with old_password and new_password
            
        Returns:
            HttpResponse: Redirects to login page on success, or shows
                         error message if old password verification fails
        """
        user = self.request.user
        if user.check_password(form.cleaned_data['old_password']):
            # Set the new password (this handles proper password hashing)
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            return super().form_valid(form)
        
        # If the old password doesn't match, add an error
        form.add_error(None, 'Old password is incorrect')
        return self.form_invalid(form)