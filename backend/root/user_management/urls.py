# backend/root/user_management/urls.py
"""
URL Configuration for User Management in UPlant

This module defines URL patterns for user authentication, account creation,
and password management using Django's template-based views. These URLs serve
traditional HTML views rather than API endpoints, which are defined separately
in api/urls.py.

URL Structure:
- /create-account/ - New user registration
- /change-password/ - Form to change password for logged-in users
- /password_reset/ - Initiates password recovery workflow
- /password_reset/done/ - Confirmation that reset email was sent
- /reset/<uidb64>/<token>/ - Link sent in reset email to verify user
- /reset/done/ - Confirmation that password reset was successful

Note: This configuration customizes Django's built-in auth views with UPlant-specific
templates, email formats, and success URLs.
"""

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from user_management.views import UserCreateView, PasswordChangeView

urlpatterns = [
    # Custom password change view for logged-in users
    # Uses our own PasswordChangeView that handles validation and success messages
    path('change-password/', 
         PasswordChangeView.as_view(), 
         name='change_password'),
    
    # ============== PASSWORD RESET WORKFLOW =============== #
    # Step 1: User requests password reset by providing email
    # Initiates the password reset process by sending an email with reset link
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(
            # Custom UPlant templates for the form and email
            template_name='user_management/email/password_reset_form.html',
            email_template_name='user_management/email/password_reset_email.html',
            subject_template_name='user_management/email/password_reset_subject.txt',
            # Where to go after form is submitted
            success_url=reverse_lazy('user_management:password_reset_done'),
            # HTML-formatted email template (for email clients that support it)
            html_email_template_name='user_management/email/password_reset_email.html',
            # The sender's email address shown in the reset email
            from_email='UPlant <uplant.notifications@gmail.com>',
         ),
         name='password_reset'),
    
    # Step 2: Confirm to user that reset email was sent
    # This view is shown after the email is sent - it doesn't perform any actions
    path('password_reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
            template_name='user_management/email/password_reset_done.html'
         ),
         name='password_reset_done'),
    
    # Step 3: User clicks link in email and enters new password
    # Validates the reset token and UID, then presents password form
    # Parameters:
    #   - uidb64: User ID encoded in base64
    #   - token: Secure token to verify reset request legitimacy
    path('reset/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
            template_name='user_management/email/password_reset_confirm.html',
            success_url=reverse_lazy('user_management:password_reset_complete')
         ),
         name='password_reset_confirm'),
    
    # Step 4: Confirmation that password was successfully reset
    # Final step in password reset workflow, shown after successful password change
    path('reset/done/', 
         auth_views.PasswordResetCompleteView.as_view(
            template_name='user_management/email/password_reset_complete.html'
         ),
         name='password_reset_complete'),
    
    # ============== USER ACCOUNT CREATION =============== #
    # New user registration using our custom view
    # Renders a form for account creation and handles form submission
    path('create-account/', 
         UserCreateView.as_view(), 
         name='create_account'),
]