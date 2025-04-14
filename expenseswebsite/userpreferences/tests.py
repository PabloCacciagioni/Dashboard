from django.test import TestCase, Client
import json
import os
from django.contrib.auth.models import User
from django.conf import settings
from django.urls import reverse
from .models import UserPreference

# Create your tests here.

class PreferencesIndexViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.url = reverse('preferences')
        
        self.currencies_path = os.path.join(settings.BASE_DIR, 'currencies.json')
        with open(self.currencies_path, 'w') as f:
            json.dump({'USD': '$', 'ARS': '$'}, f)
            
    def tearDown(self):
        if os.path.exists(self.currencies_path):
            os.remove(self.currencies_path)
            
    def test_post_index_creates_user_preferences(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.url, {'currency': 'USD'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserPreference.objects.filter(user=self.user).exists())
        self.assertEqual(UserPreference.objects.get(user=self.user).currency, 'USD')
        
    def test_post_index_update_user_preference(self):
        UserPreference.objects.create(user=self.user, currency='ARS')
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.url, {'currency': 'USD'})
        self.assertEqual(UserPreference.objects.get(user=self.user).currency, 'USD')
        