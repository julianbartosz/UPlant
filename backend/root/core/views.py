# backend/root/core/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.mail import send_mail
from core.forms import ContactForm
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.contrib import messages


def home(request):
    return render(request, 'core/home.html')
    # return render(request, 'core/home.html', {'test_message': 'BACKEND HOME PAGE - DJANGO'})

@login_required
def search_select(request):
    return render(request, 'core/search_select.html')


def about(request):
    return render(request, 'core/about.html')


def privacy(request):
    return render(request, 'core/privacy.html')


def help_page(request):
    return render(request, 'core/help.html')


def terms(request):
    return render(request, 'core/terms.html')


def contact(request):
    return render(request, 'core/contact.html')

class ContactView(FormView):
    template_name = 'core/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('home')  # Or point to a thank-you view

    def form_valid(self, form):
        subject = form.cleaned_data['subject']
        email = form.cleaned_data['email']
        message = form.cleaned_data['message']

        full_message = f"From: {email}\n\n{message}"

        send_mail(
            subject,
            full_message,
            email,  # Sender
            ['uplant.notifications@gmail.com'],  # Replace with actual recipient
            fail_silently=False,
        )

        messages.success(self.request, "Your message has been sent successfully!")
        return super().form_valid(form)