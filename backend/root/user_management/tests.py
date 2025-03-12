# backend/root/user_management/tests.py

from django.test import TestCase, Client, SimpleTestCase
from django.urls import reverse, resolve
from django.core.exceptions import ValidationError
from user_management.models import User, UserManager
from user_management.forms import CustomUserCreationForm, CustomUserUpdateForm
from user_management.views import UserCreateView, UserUpdateView, UserListView, UserDetailView
from django.contrib.auth import views as auth_views
from django.contrib.admin.sites import AdminSite
from user_management.admin import UserCreationForm, UserChangeForm, UserAdmin

#UNIT TESTS


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@test.com',
            password='testpassword',
            first_name='Test',
            last_name='User',
            role='User'
        )

    def test_create_user(self):
        self.assertEqual(self.user.email, 'testuser@test.com')
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.last_name, 'User')
        self.assertEqual(self.user.role, 'User')
        self.assertFalse(self.user.is_superuser)

    def test_create_user_no_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='testpassword')

    def test_create_superuser(self):
        superuser = User.objects.create_superuser(
            email='superuser@test.com',
            password='testpassword'
        )
        self.assertEqual(superuser.email, 'superuser@test.com')
        self.assertTrue(superuser.is_superuser)

    def test_create_superuser_no_is_superuser(self):
        with self.assertRaises(ValueError):
            User.objects.create_superuser(
                email='superuser@test.com',
                password='testpassword',
                is_superuser=False
            )

    def test_get_full_name(self):
        self.assertEqual(self.user.get_full_name(), 'Test User')

    def test_get_short_name(self):
        self.assertEqual(self.user.get_short_name(), 'Test')

    def test_is_staff(self):
        self.assertFalse(self.user.is_staff)

    def test_has_perm(self):
        self.assertFalse(self.user.has_perm('some_permission'))

    def test_has_module_perms(self):
        self.assertFalse(self.user.has_module_perms('some_app_label'))


class UserFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='testuser@test.com',
            password='testpassword',
            first_name='Test',
            last_name='User',
            role='User'
        )

    def test_custom_user_creation_form(self):
        form = CustomUserCreationForm(data={
            'email': 'newuser@test.com',
            'password1': '938efh93efh',
            'password2': '938efh93efh',
            'first_name': 'New',
            'last_name': 'User',
            'role': 'User'
        })
        if not form.is_valid():
            print(form.errors)
        self.assertTrue(form.is_valid())

    def test_custom_user_update_form(self):
        form = CustomUserUpdateForm(instance=self.user, data={
            'email': 'updateduser@test.com',
            'first_name': 'Updated',
            'last_name': 'User',
            'role': 'User'
        })
        self.assertTrue(form.is_valid())


class UserURLTest(SimpleTestCase):
    def test_create_user_url_resolves(self):
        url = reverse('user_management:create_user')
        self.assertEqual(resolve(url).func.view_class, UserCreateView)

    def test_update_user_url_resolves(self):
        url = reverse('user_management:update_user', args=[1])
        self.assertEqual(resolve(url).func.view_class, UserUpdateView)

    def test_user_list_url_resolves(self):
        url = reverse('user_management:user_list')
        self.assertEqual(resolve(url).func.view_class, UserListView)

    def test_user_detail_url_resolves(self):
        url = reverse('user_management:user_detail', args=[1])
        self.assertEqual(resolve(url).func.view_class, UserDetailView)

class MockRequest:
    pass


request = MockRequest()


class UserCreationFormTest(TestCase):
    def test_form_with_valid_data(self):
        form = UserCreationForm(data={
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'User',
            'address': 'Test Address',
            'password1': 'testpassword',
            'password2': 'testpassword'
        })
        self.assertTrue(form.is_valid())

    def test_form_with_mismatched_passwords(self):
        form = UserCreationForm(data={
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'role': 'User',
            'address': 'Test Address',
            'password1': 'testpassword',
            'password2': 'wrongpassword'
        })
        self.assertFalse(form.is_valid())

    def test_form_with_missing_fields(self):
        form = UserCreationForm(data={})
        self.assertFalse(form.is_valid())


class UserChangeFormTest(TestCase):
    def test_form_with_valid_data(self):
        user = User.objects.create(email='test@test.com', password='testpassword')
        form = UserChangeForm(instance=user, data={
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'is_active': True,
            'is_superuser': False,
            'role': 'User',
            'address': 'Test Address'
        })
        self.assertTrue(form.is_valid())

    def test_form_with_missing_fields(self):
        user = User.objects.create(email='test@test.com', password='testpassword')
        form = UserChangeForm(instance=user, data={})
        self.assertFalse(form.is_valid())


class UserAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = UserAdmin(User, self.site)

    def test_add_form(self):
        self.assertEqual(self.admin.get_form(request), UserCreationForm)

    def test_change_form(self):
        self.assertEqual(self.admin.get_form(request, obj=User()), UserChangeForm)

    def test_list_display(self):
        self.assertEqual(self.admin.get_list_display(request), ('email', 'first_name', 'last_name', 'role', 'is_active'))

    def test_search_fields(self):
        self.assertEqual(self.admin.get_search_fields(request), ('email', 'first_name', 'last_name'))

# UNIT TESTS END
# ACCEPTANCE TESTS


class UserViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            email='testuser@test.com',
            password='testpassword',
            first_name='Test',
            last_name='User',
            role='User'
        )

    def test_user_create_view(self):
        self.client.login(email='testuser@test.com', password='testpassword')
        response = self.client.get(reverse('user_management:create_user'))
        self.assertEqual(response.status_code, 200)

    def test_user_update_view(self):
        self.client.login(email='testuser@test.com', password='testpassword')
        response = self.client.get(reverse('user_management:update_user', args=[self.user.id]))
        self.assertEqual(response.status_code, 200)

    def test_user_list_view(self):
        self.client.login(email='testuser@test.com', password='testpassword')
        response = self.client.get(reverse('user_management:user_list'))
        self.assertEqual(response.status_code, 200)

    def test_user_detail_view(self):
        self.client.login(email='testuser@test.com', password='testpassword')
        response = self.client.get(reverse('user_management:user_detail', args=[self.user.id]))
        self.assertEqual(response.status_code, 200)

# ACCEPTANCE TESTS END
