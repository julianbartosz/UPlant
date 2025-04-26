# backend/root/user_management/urls.py

from django.urls import path, reverse_lazy
from django.contrib.auth import views as auth_views
from user_management.views import UserCreateView, PasswordChangeView

urlpatterns = [
    path('change-password/', PasswordChangeView.as_view(), name='change_password'),
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='user_management/email/password_reset_form.html',
        email_template_name='user_management/email/password_reset_email.html',
        subject_template_name='user_management/email/password_reset_subject.txt',
        success_url=reverse_lazy('user_management:password_reset_done'),
        html_email_template_name='user_management/email/password_reset_email.html',
        from_email='UPlant <uplant.notifications@gmail.com>',
        ),
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
    path('create-account/', UserCreateView.as_view(), name='create_account'),
]
