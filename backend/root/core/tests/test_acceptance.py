import pytest
from django.test import TestCase, Client, RequestFactory
from django.urls import resolve, reverse
from django.contrib.auth.models import User, AnonymousUser
from django.contrib.messages import get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponse
from unittest.mock import patch, MagicMock

from django.contrib.auth.views import LoginView, LogoutView
from core.views import home, search_select, about, privacy, help_page, terms, contact, ContactView
from core.forms import CustomAuthenticationForm, ContactForm


@pytest.mark.django_db
class TestUrlPatterns:
    """Tests for URL patterns in core/urls.py"""

    def test_home_url(self):
        """Test home URL pattern"""
        url = reverse('home')
        assert url == '/'
        view_func = resolve(url).func
        assert view_func == home
    
    def test_login_url(self):
        """Test login URL pattern"""
        url = reverse('login')
        assert url == '/login/'
        view_func = resolve(url).func
        assert view_func.__name__ == LoginView.as_view().__name__
        
    def test_logout_url(self):
        """Test logout URL pattern"""
        url = reverse('logout')
        assert url == '/logout/'
        view_func = resolve(url).func
        assert view_func.__name__ == LogoutView.as_view().__name__

    def test_footer_urls(self):
        """Test footer page URL patterns"""
        url_view_pairs = [
            ('about', '/about/', about),
            ('privacy', '/privacy/', privacy),
            ('help', '/help/', help_page),
            ('terms', '/terms/', terms),
            ('contact', '/contact/', None)  # ContactView tested separately
        ]
        
        for name, path, view_func in url_view_pairs:
            url = reverse(name)
            assert url == path
            resolved = resolve(url)
            
            if view_func:
                assert resolved.func == view_func
            else:
                assert resolved.func.__name__ == ContactView.as_view().__name__

    def test_contact_url_class_based_view(self):
        """Test that contact URL resolves to ContactView"""
        url = reverse('contact')
        assert url == '/contact/'
        view_class = resolve(url).func.view_class
        assert view_class == ContactView


@pytest.mark.django_db
class TestBasicViews:
    """Tests for basic view functions in core/views.py"""
    
    @pytest.fixture
    def client(self):
        return Client()
    
    @pytest.fixture
    def authenticated_client(self, client, django_user_model):
        user = django_user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        client.login(username='testuser', password='testpassword')
        return client

    @pytest.mark.parametrize('view_name,template', [
        ('home', 'core/home.html'),
        ('about', 'core/about.html'),
        ('privacy', 'core/privacy.html'),
        ('help', 'core/help.html'),
        ('terms', 'core/terms.html'),
        ('contact', 'core/contact.html')
    ])
    def test_basic_views(self, client, view_name, template):
        """Test that basic views render correct templates"""
        response = client.get(reverse(view_name))
        assert response.status_code == 200
        assert template in [t.name for t in response.templates]


@pytest.mark.django_db
class TestContactView:
    """Tests for the ContactView class-based view"""
    
    @pytest.fixture
    def client(self):
        return Client()
    
    def test_get_contact_view(self, client):
        """Test GET request to ContactView"""
        response = client.get(reverse('contact'))
        assert response.status_code == 200
        assert 'form' in response.context
        assert isinstance(response.context['form'], ContactForm)
        assert 'core/contact.html' in [t.name for t in response.templates]
    
    def test_contact_view_uses_correct_form(self, client):
        """Test that ContactView uses ContactForm"""
        response = client.get(reverse('contact'))
        assert isinstance(response.context['form'], ContactForm)
    
    @patch('core.views.send_mail')
    def test_successful_form_submission(self, mock_send_mail, client):
        """Test successful form submission"""
        form_data = {
            'subject': 'Test Subject',
            'email': 'test@example.com',
            'message': 'Test message content'
        }
        
        response = client.post(reverse('contact'), form_data)
        
        # Check email sending
        assert mock_send_mail.called
        args = mock_send_mail.call_args[0]
        assert args[0] == 'Test Subject'
        assert 'test@example.com' in args[1]
        assert args[2] == 'test@example.com'
        assert args[3] == ['uplant.notifications@gmail.com']
        
        # Check redirect
        assert response.status_code == 302
        assert response.url == reverse('home')
        
        # Check message
        messages = list(get_messages(response.wsgi_request))
        assert len(messages) == 1
        assert "Your message has been sent successfully!" in str(messages[0])
    
    @patch('core.views.send_mail')
    def test_invalid_form_submission(self, mock_send_mail, client):
        """Test invalid form submission"""
        # Missing required fields
        form_data = {
            'subject': '',
            'email': 'invalid-email',
            'message': ''
        }
        
        response = client.post(reverse('contact'), form_data)
        
        # Email should not be sent
        assert not mock_send_mail.called
        
        # Form should be redisplayed with errors
        assert response.status_code == 200
        form = response.context['form']
        assert not form.is_valid()
        assert 'subject' in form.errors
        assert 'email' in form.errors
        assert 'message' in form.errors
    
    @patch('core.views.send_mail')
    def test_form_subject_too_long(self, mock_send_mail, client):
        """Test form validation with subject too long"""
        form_data = {
            'subject': 'X' * 101,  # Over 100 characters
            'email': 'test@example.com',
            'message': 'Test message'
        }
        
        response = client.post(reverse('contact'), form_data)
        
        # Check form validation error
        assert response.status_code == 200
        form = response.context['form']
        assert not form.is_valid()
        assert 'subject' in form.errors
        assert 'Ensure this value has at most 100 characters' in str(form.errors['subject'])
    
    @patch('core.views.send_mail', side_effect=Exception("Email sending failed"))
    def test_email_sending_failure(self, mock_send_mail, client):
        """Test handling of email sending failure"""
        form_data = {
            'subject': 'Test Subject',
            'email': 'test@example.com',
            'message': 'Test message content'
        }
        
        with pytest.raises(Exception):
            client.post(reverse('contact'), form_data)


class TestViewsWithRequestFactory:
    """Tests for views using RequestFactory for more direct testing"""
    
    @pytest.fixture
    def factory(self):
        return RequestFactory()
    
    @pytest.fixture
    def user(self, django_user_model):
        return django_user_model.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
    
    def test_home_view_direct(self, factory):
        """Test home view directly"""
        request = factory.get('/')
        response = home(request)
        assert response.status_code == 200
    
    def test_home_view(self, client):
        response = client.get(reverse('home'))
        assert response.status_code == 200
        assert 'core/home.html' in [t.name for t in response.templates]
    
    def test_search_select_view_authenticated(self, factory, user):
        """Test search_select view with authenticated user"""
        request = factory.get('/search-select/')
        request.user = user
        response = search_select(request)
        assert response.status_code == 200
    
    def test_search_select_view_unauthenticated(self, factory):
        """Test search_select view with unauthenticated user"""
        request = factory.get('/search-select/')
        request.user = AnonymousUser()
        
        # Manually handle login_required redirect
        response = search_select(request)
        assert response.status_code == 302
        assert 'login' in response.url
    
    def test_static_page_views(self, factory):
        """Test all static page views directly"""
        view_funcs = [about, privacy, help_page, terms, contact]
        templates = ['about.html', 'privacy.html', 'help.html', 'terms.html', 'contact.html']
        
        for view_func, template in zip(view_funcs, templates):
            request = factory.get('/')
            response = view_func(request)
            assert response.status_code == 200


class TestContactViewClass:
    """Direct tests for ContactView class methods"""
    
    @pytest.fixture
    def factory(self):
        return RequestFactory()
    
    def setup_request(self, request):
        """Add session and messages middleware to request"""
        middleware = SessionMiddleware(lambda x: None)
        middleware.process_request(request)
        request.session.save()
        
        middleware = MessageMiddleware(lambda x: None)
        middleware.process_request(request)
        return request
    
    @patch('core.views.send_mail')
    @pytest.mark.django_db
    def test_form_valid_method(self, mock_send_mail, factory):
        """Test ContactView.form_valid method directly"""
        # Create form with valid data
        form = ContactForm(data={
            'subject': 'Test Subject',
            'email': 'test@example.com',
            'message': 'Test message'
        })
        assert form.is_valid()
        
        # Create request and contact view
        request = factory.post('/contact/')
        request = self.setup_request(request)
        
        view = ContactView()
        view.request = request
        view.setup(request)
        
        # Call form_valid method directly
        response = view.form_valid(form)
        
        # Check email was sent
        assert mock_send_mail.called
        
        # Check success message was added
        messages = list(get_messages(request))
        assert len(messages) == 1
        assert "Your message has been sent successfully!" in str(messages[0])
        
        # Check redirect to success URL
        assert response.status_code == 302
        assert response.url == reverse('home')


@pytest.mark.django_db
class TestViewsWithEdgeCases:
    """Test views with edge cases and unusual scenarios"""
    
    @pytest.fixture
    def client(self):
        return Client()
    
    def test_contact_view_empty_post(self, client):
        """Test POST request to contact view with empty data"""
        response = client.post(reverse('contact'), {})
        assert response.status_code == 200
        assert 'form' in response.context
        assert not response.context['form'].is_valid()
    
    def test_contact_view_partial_data(self, client):
        """Test POST request with some fields missing"""
        response = client.post(reverse('contact'), {'subject': 'Test'})
        assert response.status_code == 200
        assert 'form' in response.context
        assert not response.context['form'].is_valid()
        assert 'email' in response.context['form'].errors
        assert 'message' in response.context['form'].errors
    
    def test_login_view_with_custom_form(self, client):
        """Test that login view uses CustomAuthenticationForm"""
        response = client.get(reverse('login'))
        assert response.status_code == 200
        assert 'form' in response.context
        assert isinstance(response.context['form'], CustomAuthenticationForm)
    
    def test_logout_redirects_to_home(self, client, django_user_model):
        """Test logout redirects to home page"""
        user = django_user_model.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='testpassword'
        )
        client.login(username='testuser', password='testpassword')
        response = client.post(reverse('logout'))
        assert response.status_code == 302
        assert response.url == reverse('home')