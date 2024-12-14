from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from user.forms import RegisterForm, LoginForm

class UserViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='existinguser',
            password='testpass123'
        )

    def test_register_view_get(self):
        """Test register view GET request"""
        response = self.client.get(reverse('users:register'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'register.html')
        self.assertIsInstance(response.context['form'], RegisterForm)

    def test_register_view_post_valid(self):
        """Test register view with valid POST data"""
        data = {
            'username': 'newuser',
            'password': 'newpass123',
            'confirm': 'newpass123'
        }
        response = self.client.post(reverse('users:register'), data)
        self.assertEqual(response.status_code, 302)  # Should redirect to index
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Check if user is logged in
        user = User.objects.get(username='newuser')
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_register_view_post_invalid(self):
        """Test register view with invalid POST data"""
        data = {
            'username': '',  # Invalid: empty username
            'password': 'newpass123',
            'confirm': 'newpass123'
        }
        response = self.client.post(reverse('users:register'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())

    def test_login_view_get(self):
        """Test login view GET request"""
        response = self.client.get(reverse('users:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertIsInstance(response.context['form'], LoginForm)

    def test_login_view_post_valid(self):
        """Test login view with valid credentials"""
        data = {
            'username': 'existinguser',
            'password': 'testpass123'
        }
        response = self.client.post(reverse('users:login'), data)
        self.assertEqual(response.status_code, 302)  # Should redirect to index
        
        # Check if user is logged in
        self.assertEqual(int(self.client.session['_auth_user_id']), self.user.pk)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(message.tags == 'success' for message in messages))

    def test_login_view_post_invalid(self):
        """Test login view with invalid credentials"""
        data = {
            'username': 'existinguser',
            'password': 'wrongpassword'
        }
        response = self.client.post(reverse('users:login'), data)
        self.assertEqual(response.status_code, 200)
        
        # Check for error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(message.tags == 'info' for message in messages))

    def test_logout_view(self):
        """Test logout view"""
        # First login
        self.client.login(username='existinguser', password='testpass123')
        
        # Then logout
        response = self.client.get(reverse('users:logout'))
        self.assertEqual(response.status_code, 302)  # Should redirect to index
        
        # Check if user is logged out
        self.assertNotIn('_auth_user_id', self.client.session)
        
        # Check for success message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(message.tags == 'success' for message in messages))

class UserFormsTest(TestCase):
    def test_register_form_valid(self):
        """Test register form with valid data"""
        form_data = {
            'username': 'testuser',
            'password': 'testpass123',
            'confirm': 'testpass123'
        }
        form = RegisterForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_register_form_passwords_dont_match(self):
        """Test register form with non-matching passwords"""
        form_data = {
            'username': 'testuser',
            'password': 'testpass123',
            'confirm': 'differentpass123'
        }
        form = RegisterForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_login_form_valid(self):
        """Test login form with valid data"""
        form_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_login_form_invalid(self):
        """Test login form with invalid data"""
        form_data = {
            'username': '',  # Invalid: empty username
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())