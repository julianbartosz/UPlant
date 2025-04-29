import pytest
from django import forms
from django.test import TestCase
from django.contrib.auth.forms import AuthenticationForm

from core.forms import CustomAuthenticationForm, ContactForm


class TestCustomAuthenticationForm:
    """Tests for CustomAuthenticationForm"""
    
    def test_form_fields(self):
        """Test that the form has the expected fields"""
        form = CustomAuthenticationForm()
        assert 'username' in form.fields
        assert 'password' in form.fields
        
    def test_username_field_type(self):
        """Test that the username field is an EmailField"""
        form = CustomAuthenticationForm()
        assert isinstance(form.fields['username'], forms.EmailField)
        
    def test_username_field_label(self):
        """Test that the username field label is set to 'Email'"""
        form = CustomAuthenticationForm()
        assert form.fields['username'].label == 'Email'
        
    def test_username_field_widget(self):
        """Test that the username field widget is EmailInput with autofocus"""
        form = CustomAuthenticationForm()
        assert isinstance(form.fields['username'].widget, forms.EmailInput)
        assert form.fields['username'].widget.attrs.get('autofocus') is True
        
    def test_form_inheritance(self):
        """Test that the form inherits from AuthenticationForm"""
        assert issubclass(CustomAuthenticationForm, AuthenticationForm)
        
    def test_valid_email_validation(self):
        """Test form validation with valid email"""
        data = {
            'username': 'valid@example.com',
            'password': 'password123'
        }
        form = CustomAuthenticationForm(data=data)
        assert 'username' not in form.errors
        
    def test_invalid_email_validation(self):
        """Test form validation with invalid email"""
        data = {
            'username': 'invalid-email',
            'password': 'password123'
        }
        form = CustomAuthenticationForm(data=data)
        assert 'username' in form.errors
        assert 'Enter a valid email address' in str(form.errors['username'])
        
    def test_required_fields(self):
        """Test that all fields are required"""
        form = CustomAuthenticationForm(data={})
        assert not form.is_valid()
        assert 'username' in form.errors
        assert 'password' in form.errors
        assert 'This field is required' in str(form.errors['username'])
        assert 'This field is required' in str(form.errors['password'])


class TestContactForm:
    """Tests for ContactForm"""
    
    def test_form_fields(self):
        """Test that the form has the expected fields"""
        form = ContactForm()
        assert 'subject' in form.fields
        assert 'email' in form.fields
        assert 'message' in form.fields
        
    def test_subject_field(self):
        """Test subject field properties"""
        form = ContactForm()
        assert isinstance(form.fields['subject'], forms.CharField)
        assert form.fields['subject'].max_length == 100
        assert form.fields['subject'].label == 'Subject'
        
    def test_email_field(self):
        """Test email field properties"""
        form = ContactForm()
        assert isinstance(form.fields['email'], forms.EmailField)
        assert form.fields['email'].label == 'Your Email'
        
    def test_message_field(self):
        """Test message field properties"""
        form = ContactForm()
        assert isinstance(form.fields['message'], forms.CharField)
        assert isinstance(form.fields['message'].widget, forms.Textarea)
        assert form.fields['message'].label == 'Message'
        
    def test_form_validation_with_valid_data(self):
        """Test form validation with valid data"""
        data = {
            'subject': 'Test Subject',
            'email': 'test@example.com',
            'message': 'This is a test message.'
        }
        form = ContactForm(data=data)
        assert form.is_valid()
        
    def test_form_validation_with_invalid_email(self):
        """Test form validation with invalid email"""
        data = {
            'subject': 'Test Subject',
            'email': 'invalid-email',
            'message': 'This is a test message.'
        }
        form = ContactForm(data=data)
        assert not form.is_valid()
        assert 'email' in form.errors
        assert 'Enter a valid email address' in str(form.errors['email'])
        
    def test_form_validation_with_long_subject(self):
        """Test form validation with too long subject"""
        data = {
            'subject': 'A' * 101,  # 101 characters, max is 100
            'email': 'test@example.com',
            'message': 'This is a test message.'
        }
        form = ContactForm(data=data)
        assert not form.is_valid()
        assert 'subject' in form.errors
        assert 'Ensure this value has at most 100 characters' in str(form.errors['subject'])
        
    def test_form_validation_with_empty_message(self):
        """Test form validation with empty message"""
        data = {
            'subject': 'Test Subject',
            'email': 'test@example.com',
            'message': ''
        }
        form = ContactForm(data=data)
        assert not form.is_valid()
        assert 'message' in form.errors
        assert 'This field is required' in str(form.errors['message'])
        
    def test_form_validation_with_missing_fields(self):
        """Test form validation with missing fields"""
        form = ContactForm(data={})
        assert not form.is_valid()
        assert len(form.errors) == 3  # All fields are required
        assert 'subject' in form.errors
        assert 'email' in form.errors
        assert 'message' in form.errors
        
    def test_boundary_values(self):
        """Test form validation with boundary values"""
        # Test with exactly 100 characters for subject (should pass)
        data = {
            'subject': 'A' * 100,
            'email': 'test@example.com',
            'message': 'This is a test message.'
        }
        form = ContactForm(data=data)
        assert form.is_valid()