# tests.py
from django.test import TestCase, Client
from django.urls import reverse, resolve
from django.contrib.auth.views import LoginView, LogoutView
from django import forms
from core.views import home, search_select
from core.forms import CustomAuthenticationForm

# UNIT TESTS

class UrlsTest(TestCase):
    """
    This class contains tests for the URL configurations in core/urls.py.
    """
    def test_home_url(self):
        """
        This test checks the home URL. It asserts that the URL pattern named 'home' resolves to the home view function.
        """
        url = reverse('home')
        self.assertEqual(resolve(url).func, home)

    def test_search_select_url(self):
        """
        This test checks the search_select URL. It asserts that the URL pattern named 'search_select' resolves to the search_select view function.
        """
        url = reverse('search_select')
        self.assertEqual(resolve(url).func, search_select)

# UNIT TESTS END
# ACCEPTANCE TESTS


class HomeViewTest(TestCase):
    """
    This class contains tests for the home view.
    """
    def setUp(self):
        """
        This method sets up the test case with a client. It is run before each test method.
        """
        self.client = Client()

    def test_home_view(self):
        """
        This test checks the home view. It asserts that the response status code is 200 and the correct template is used.
        """
        response = self.client.get(reverse('home'))  # Replace 'home' with the actual name of the URL pattern for the home view
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/home.html')


class SearchSelectViewTest(TestCase):
    """
    This class contains tests for the search_select view.
    """
    def setUp(self):
        """
        This method sets up the test case with a client. It is run before each test method.
        """
        self.client = Client()

    def test_search_select_view(self):
        """
        This test checks the search_select view. It asserts that the response status code is 200 and the correct template is used.
        """
        response = self.client.get(reverse('search_select'))  # Replace 'search_select' with the actual name of the URL pattern for the search_select view
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'core/search_select.html')

# ACCEPTANCE TESTS END
