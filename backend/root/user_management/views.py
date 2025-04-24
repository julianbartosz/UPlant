# backend/root/user_management/views.py

from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from user_management.forms import CustomUserCreationForm, CustomPasswordChangeForm
from user_management.models import User
from django.db.models import Q
from django.contrib import messages

class UserCreateView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'user_management/create_user.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        # Add debugging
        print("Form is valid!")
        response = super().form_valid(form)
        messages.success(self.request, "Your account has been created successfully!")
        return response
    
    def form_invalid(self, form):
        # Add debugging
        print("Form is invalid!")
        print(form.errors)
        return super().form_invalid(form)
    
class PasswordChangeView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = CustomPasswordChangeForm
    template_name = 'user_management/change_password.html'
    success_url = reverse_lazy('core:login')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        user = self.request.user
        if user.check_password(form.cleaned_data['old_password']):
            user.set_password(form.cleaned_data['new_password'])
            user.save()
            return super().form_valid(form)
        form.add_error(None, 'Old password is incorrect')
        return self.form_invalid(form)