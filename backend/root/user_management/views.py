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

#my changes
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

class ForumListView(LoginRequiredMixin, ListView):
    model = Forums
    template_name = 'user_management/forum_list.html'
    context_object_name = 'forums'

    def get_queryset(self):
        return Forums.objects.filter(is_deleted=False).annotate(reply_count=models.Count('replies')).order_by('-created_at')


class ForumDetailView(LoginRequiredMixin, DetailView):
    model = Forums
    template_name = 'user_management/forum_detail.html'
    context_object_name = 'forum'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['replies'] = Replies.objects.filter(forum_id=self.object, is_deleted=False).annotate(
            like_count=models.Count('likes'),
            reply_count=models.Count('replies')
        ).order_by('-created_at')
        context['reply_form'] = ReplyForm()
        return context


class CreateForumView(LoginRequiredMixin, CreateView):
    model = Forums
    form_class = ForumForm
    template_name = 'user_management/create_forum.html'
    success_url = reverse_lazy('forum_list')

    def form_valid(self, form):
        form.instance.user_id = self.request.user
        messages.success(self.request, "Your forum has been created!")
        return super().form_valid(form)


class ReplyView(LoginRequiredMixin, View):
    def post(self, request, forum_id, parent_id=None):
        forum = get_object_or_404(Forums, pk=forum_id)
        form = ReplyForm(request.POST)
        if form.is_valid():
            reply = form.save(commit=False)
            reply.user_id = request.user
            reply.forum_id = forum
            if parent_id:
                reply.parent_id = get_object_or_404(Replies, pk=parent_id)
            reply.save()
            messages.success(request, "Your reply has been posted.")
        else:
            messages.error(request, "There was an error posting your reply.")
        return redirect('user_management:forum_detail', pk=forum.id)

class LikeReplyView(LoginRequiredMixin, View):
    def post(self, request, forum_id, reply_id):
        reply = get_object_or_404(Replies, pk=reply_id)
        like, created = Likes.objects.get_or_create(user_id=request.user, reply_id=reply)
        if not created:
            like.delete()
            messages.success(request, "You unliked this reply.")
        else:
            messages.success(request, "You liked this reply.")
        return redirect('user_management:forum_detail', pk=forum_id)  # Use forum_id for redirection
