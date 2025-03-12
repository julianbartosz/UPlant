from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from user_management.models import User
from django.core.mail import send_mail

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'username', 'role')

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['role'].choices = [('User', 'User')]


class CustomUserUpdateForm(UserChangeForm):
    password = None

    class Meta:
        model = User
        fields = ('email', 'username', 'role')

    def __init__(self, *args, **kwargs):
        super(CustomUserUpdateForm, self).__init__(*args, **kwargs)
        self.fields['email'].disabled = True


class CustomPasswordChangeForm(forms.ModelForm):
    old_password = forms.CharField(label='Old Password', widget=forms.PasswordInput)
    new_password = forms.CharField(label='New Password', widget=forms.PasswordInput)
    confirm_password = forms.CharField(label='Confirm New Password', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ()

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', 'New password and Confirm new password do not match')
        return cleaned_data
    
    # Cainan work from 3/12
    class ContactForm(forms.Form):
        name = forms.CharField(
            max_length=100, 
            widget=forms.TextInput(attrs={'placeholder': 'Enter your name', 'class': 'form-control'})
        )
        subject = forms.CharField(
            max_length=100, 
            widget=forms.TextInput(attrs={'placeholder': 'Enter subject', 'class': 'form-control'})
        )
        message = forms.CharField(
            widget=forms.Textarea(attrs={'placeholder': 'Describe your problem', 'class': 'form-control', 'rows': 4})
        )
        #END