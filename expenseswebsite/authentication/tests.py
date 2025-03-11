from django.test import TestCase, Client
from django.contrib.auth import get_user_model, get_user
import json
from django.contrib.messages import get_messages
from django.urls import reverse


# Create your tests here.
class EmailValidationViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = '/authentication/validate-email'
        self.user = get_user_model().objects.create_user(username="testuser", email='existing@example.com', password='password123')
        
    def test_invalid_email(self):
        response = self.client.post(self.url, json.dumps({'email': 'invalid-email'}), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('email_error', response.json())
        
    def test_invalid_email(self):
        response = self.client.post(self.url, json.dumps({'email': 'existing@example.com'}), content_type='application/json')
        self.assertEqual(response.status_code, 409)
        self.assertIn('email_error', response.json())
        
    def test_valid_email(self):
        response = self.client.post(self.url, json.dumps({'email': 'new@example.com'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('email_valid', response.json())   
        
class UsernameValidationViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = '/authentication/validate-username'
        self.user = get_user_model().objects.create_user(username='existinguser', email='existing@example.com', password='password123')
        
    def test_validate_username(self):
        response = self.client.post(self.url, json.dumps({'username': 'invalid_user!@#'}), content_type='application/json')
        self.assertEqual(response.status_code, 409)
        self.assertIn('username_error', response.json())
        
    def test_validate_username(self):
        response = self.client.post(self.url, json.dumps({'username': 'existinguser'}), content_type='application/json')
        self.assertEqual(response.status_code, 409)
        self.assertIn('username_error', response.json())
    
    def test_validate_username(self):
        response = self.client.post(self.url, json.dumps({'username': 'newuser'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('username_valid', response.json())
        
class RegistrationViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = '/authentication/register'
        self.user = get_user_model().objects.create_user(username='existinguser', email='existing@example.com', password='password123')
        
    def test_get_registration_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/register.html')
        
    def test_successful_registration(self):
        response = self.client.post(self.url, {'username': 'newuser', 'email': 'new@example.com', 'password': 'validpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(get_user_model().objects.filter(username='newuser'). exists())
        
        messages = [msg.message for msg in get_messages(response.wsgi_request)]
        self.assertIn('Account successfully created', messages)
        
    def test_email_already_exists(self):
        response = self.client.post(self.url, {'username': 'newuser', 'email': 'existing@example.com', 'password': 'validpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_user_model().objects.filter(username='newuser').count(), 0)
        
    def test_username_already_exists(self):
        response = self.client.post(self.url, {'username': 'existinguser', 'email': 'new@example.com', 'password': 'validpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_user_model().objects.filter(email='new@example.com').count(), 0)
        
    def test_password_too_short(self):
        response = self.client.post(self.url, {'username': 'newuser', 'email': 'new@example.com', 'password': '123'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_user_model().objects.filter(email='new@example.com').count(), 0)
        messages = [msg.message for msg in get_messages(response.wsgi_request)]
        self.assertIn('Password too short', messages)
        
class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = '/authentication/login'
        self.user = get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')
        
    def test_get_login_page(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/login.html')
        
    def test_successful_login(self):
        response = self.client.post(self.url, {'username': 'testuser', 'password': 'password123'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('expenses'))
        
    def test_invalid_credentials(self):
        response = self.client.post(self.url, {'username': 'testuser', 'password': 'wrongpassword'})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/login.html')
        messages = [msg.message for msg in get_messages(response.wsgi_request)]
        self.assertIn('Invalid credentials, try again', messages)
        
    def test_missing_fields(self):
        response = self.client.post(self.url, {'username': '', 'password': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'authentication/login.html')
        messages = [msg.message for msg in get_messages(response.wsgi_request)]
        self.assertIn('Please fill all fields', messages)
        
class LogoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = '/authentication/logout'
        self.user = get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.client.login(username='testuser', password='password123')
        
    def test_successful_logout(self):
        response = self.client.post(self.url)
        user = get_user(self.client)
        self.assertFalse(user.is_authenticated)
        
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('login'))
        
    def test_logout_message(self):
        response = self.client.post(self.url, follow=True)
        messages = [msg.message for msg in get_messages(response.wsgi_request)]
        self.assertIn('You have been logged out', messages)