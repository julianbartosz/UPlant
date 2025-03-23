# backend/root/user_management/urls.py

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from user_management.views import UserCreateView, UserUpdateView, UserListView, UserDetailView, PasswordChangeView, UserDeleteView, CreateProfileView, View
from user_management.views import ForumListView, ForumDetailView, CreateForumView, ReplyView, LikeReplyView


urlpatterns = [
    path('create/', UserCreateView.as_view(), name='create_user'),
    path('update/<int:pk>/', UserUpdateView.as_view(), name='update_user'),
    path('', UserListView.as_view(), name='user_list'),
    path('user/<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('delete/<int:pk>/', UserDeleteView.as_view(), name='user_confirm_delete'),
    path('change-password/', PasswordChangeView.as_view(), name='change_password'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='user_management/email/password_reset_form.html',
        email_template_name='user_management/email/password_reset_email.html',
        subject_template_name='user_management/email/password_reset_subject.txt',
        success_url=reverse_lazy('user_management:password_reset_done')),
        name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='user_management/email/password_reset_done.html'),
        name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='user_management/email/password_reset_confirm.html',
        success_url=reverse_lazy('user_management:password_reset_complete')),
        name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='user_management/email/password_reset_complete.html'),
        name='password_reset_complete'),
    # New Paths
    path('create-profile/', CreateProfileView.as_view(), name='create_profile'),
    path('forums/<int:forum_id>/reply/', ReplyView.as_view(), name='forum_reply'),
    path('forum/<int:forum_id>/reply/<int:parent_id>/reply/', ReplyView.as_view(), name='reply_to_reply'),
    path('forum/<int:forum_id>/reply/<int:reply_id>/like/', LikeReplyView.as_view(), name='like_reply'),
    path('forums/', ForumListView.as_view(), name='forum_list'),  
    path('forum/<int:pk>/', ForumDetailView.as_view(), name='forum_detail'),  
    path('create/forum/', CreateForumView.as_view(), name='create_forum'),  
    #New Paths END
]
