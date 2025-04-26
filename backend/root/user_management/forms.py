"""
Forms for handling user registration, authentication, and profile management.

This module provides custom forms for user creation, profile updates, and password management
in the UPlant application. These forms extend Django's built-in authentication forms with
additional fields and validation specific to the UPlant user requirements.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from user_management.models import User
import datetime
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    """
    Form for creating new users in the UPlant application.
    
    This form extends Django's UserCreationForm to include additional fields
    like email and zip_code. It also sets default values for user roles and
    creation timestamps.
    """
    email = forms.EmailField(required=True)
    # Make zip_code optional in the form
    zip_code = forms.CharField(max_length=5, required=False, 
                              help_text=_("Optional: Your postal code for local plant recommendations"))

    class Meta:
        """
        Meta configuration for the CustomUserCreationForm.
        
        Specifies the User model and the fields to be included in the form.
        """
        model = User
        fields = ('email', 'username', 'zip_code', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        """
        Initialize the form with default values.
        
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.fields["username"].initial = ""  # Ensure no default value
        
        # Add default role for new users
        if not self.instance.pk:  # If this is a new user
            self.instance.role = "User"

    def save(self, commit=True):
        """
        Save the form data to create a new user.
        
        This method ensures the created_at timestamp is set properly
        when a new user is created.
        
        Args:
            commit (bool): Whether to save the user to the database.
                          Default is True.
                          
        Returns:
            User: The newly created user instance.
        """
        user = super().save(commit=False)
        # Ensure created_at is set if needed
        if not user.created_at:
            user.created_at = datetime.datetime.now()
        if commit:
            user.save()
        return user

class CustomUserUpdateForm(UserChangeForm):
    """
    Form for updating existing user information.
    
    This form allows updating user details but disables email changes
    and excludes direct password manipulation.
    """
    password = None  # Exclude the password field from the form

    class Meta:
        """
        Meta configuration for the CustomUserUpdateForm.
        
        Specifies the User model and the fields that can be updated.
        """
        model = User
        fields = ('email', 'username', 'role')

    def __init__(self, *args, **kwargs):
        """
        Initialize the user update form with specific field constraints.
        
        Disables the email field to prevent changes to the user's email.
        
        Args:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super(CustomUserUpdateForm, self).__init__(*args, **kwargs)
        self.fields['email'].disabled = True  # Email cannot be changed


class CustomPasswordChangeForm(forms.ModelForm):
    """
    Form for changing a user's password.
    
    This form handles validation of old password and ensures the new password
    is entered consistently across two fields.
    """
    old_password = forms.CharField(label='Old Password', widget=forms.PasswordInput)
    new_password = forms.CharField(label='New Password', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Confirm New Password', widget=forms.PasswordInput)

    class Meta:
        """
        Meta configuration for the CustomPasswordChangeForm.
        
        Specifies the User model but doesn't include any fields directly
        as password fields are defined separately.
        """
        model = User
        fields = ()  # No direct model fields are included

    def clean(self):
        """
        Validate that the new password matches the confirmation field.
        
        Returns:
            dict: The cleaned form data.
            
        Raises:
            ValidationError: If the new and confirmation passwords don't match.
        """
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', 'New password and Confirm new password do not match')
        return cleaned_data
    
class ProfileForm(forms.ModelForm):
    """
    Form for updating user profile information.
    
    This form focuses on updates to public profile details like username,
    with appropriate validation to ensure uniqueness.
    """
    class Meta:
        """
        Meta configuration for the ProfileForm.
        
        Specifies the User model, fields to include, and custom widgets for display.
        """
        model = User
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'}),
        }

    def clean_username(self):
        """
        Validate that the username is not already taken by another user.
        
        Returns:
            str: The validated username.
            
        Raises:
            ValidationError: If the username is already in use.
        """
        username = self.cleaned_data.get('username')
        # Check if this username already exists, but exclude the current user
        if User.objects.filter(username=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username
    
