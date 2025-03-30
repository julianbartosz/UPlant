# backend/root/user_management/views.py

from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, ListView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from user_management.forms import CustomUserCreationForm, CustomUserUpdateForm, CustomPasswordChangeForm, ProfileForm
from user_management.models import User
from django.core.mail import send_mail
from django.db.models import Q, Count

# DELETE IN PRODUCTION
from django.http import HttpResponse
from django.core.mail import send_mail

def test_email(request):
    send_mail(
        'Test Email from UPlant',
        'This is a test email from UPlant.',
        'UPlant <uplant.notifications@gmail.com>',
        ['jbartosz@uwm.edu'],
        fail_silently=False,
    )
    return HttpResponse("Test email sent. Check your inbox.")
# DELETE IN PRODUCTION END

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    template_name = 'user_management/user_confirm_delete.html'
    success_url = reverse_lazy('user_management:user_list')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.id == self.kwargs['pk']


class UserCreateView(CreateView):
    model = User
    form_class = CustomUserCreationForm
    template_name = 'user_management/create_user.html'
    success_url = reverse_lazy('user_management:user_list')


class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    form_class = CustomUserUpdateForm
    template_name = 'user_management/update_user.html'
    success_url = reverse_lazy('user_management:user_list')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.id == self.kwargs['pk']


class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'user_management/user_list.html'
    context_object_name = 'users'

    def get_queryset(self):
        queryset = super().get_queryset()

        search_query = self.request.GET.get('search', '')

        if search_query:
            queryset = queryset.filter(Q(first_name__icontains=search_query) | Q(last_name__icontains=search_query))

        return queryset

    def test_func(self):
        return self.request.user.role in ['Supervisor', 'User']


class UserDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = User
    template_name = 'user_management/user_detail.html'
    context_object_name = 'user'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.role == 'User' or self.request.user.id == self.kwargs['pk'] or self.request.user.role == 'Supervisor'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context

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

class CreateProfileView(LoginRequiredMixin, View):
    def get(self, request):
        form = ProfileForm(instance=request.user)
        return render(request, 'user_management/createprofile.html', {'form': form})

    def post(self, request):
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully!")
            return redirect('forum_home')  # Redirect to the discussion board
        return render(request, 'user_management/createprofile.html', {'form': form})