# backend/root/user_management/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from user_management.models import User, Replies

#New Imports
from django.core.exceptions import ValidationError
from .models import Forums, Replies
#NEw Imports END



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
    
 #New Forms
class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your username'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("This username is already taken. Please choose another.")
        return username
    
class ForumForm(forms.ModelForm):
    class Meta:
        model = Forums
        fields = ['title', 'body']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter forum title'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter forum content'}),
        }

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Replies
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter your reply'}),
        }
#New Form END