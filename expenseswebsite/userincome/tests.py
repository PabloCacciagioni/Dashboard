from django.test import TestCase, Client
from django.contrib.auth.models import User
from userincome.models import UserIncome, Source
from django.utils.timezone import now
from django.urls import reverse
import json
from userpreferences.models import UserPreference
from datetime import date
import datetime

class UserIncomeModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.source = Source.objects.create(name='Salary')
        self.income1 = UserIncome.objects.create(
            owner = self.user,
            amount = 1000.50,
            date = now().date(),
            description = 'Monthly salary',
            source = self.source.name
        )
        self.income2 = UserIncome.objects.create(
            owner = self.user,
            amount = 500.00,
            date = now().date(),
            description = 'Freelance job',
            source = 'Freelancing'
        )
        
    def test_userincome_creation(self):
        self.assertEqual(UserIncome.objects.count(), 2)
        
    def test_user_income_str_method(self):
        self.assertEqual(str(self.income1), 'Salary')
        
    def test_source_creation(self):
        source = Source.objects.create(name='Investment')
        self.assertEqual(str(source), 'Investment')
        
    def test_income_ordering(self):
        incomes = UserIncome.objects.all()
        self.assertGreaterEqual(incomes[0].date, incomes[1].date)
        
    def test_user_income_relationship(self):
        self.assertEqual(self.income1.owner, self.user)
        
class SearchIncomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@prueba.com', password='password123')
        self.income1 = UserIncome.objects.create(
            owner = self.user, 
            amount = 1000.50,
            date = now().date(),
            description = 'Freelance payment',
            source = 'Salary'
        )
        self.income2 = UserIncome.objects.create(
            owner = self.user,
            amount = 500.00,
            date = now().date(),
            description = 'Salary deposit',
            source = 'salary'
        )
        self.url = reverse('search-income')
        
    def test_search_income_authenticated(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.url, json.dumps({'searchText': 'Freelance'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['description'], 'Freelance payment')
        
    def test_search_income_unauthenticated(self):
        response = self.client.post(self.url, json.dumps({'searchText': 'Salary'}), content_type='application/json')
        self.assertEqual(response.status_code, 302)
        
class IndexViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@prueba.com', password='password123')
        self.source = Source.objects.create(name='Freelance')
        self.preference = UserPreference.objects.create(user=self.user, currency='USD')
        
        for i in range(5):
            UserIncome.objects.create(
                owner = self.user,
                amount = 100 * (i + 1),
                date = now().date(),
                description = f'Income {i}',
                source = 'Freelance'
            )
            
        self.url = reverse('income')
        
    def test_index_authenticated_user(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'income/index.html')
        self.assertIn('income', response.context)
        self.assertEqual(response.context['currency'], 'USD')
        
    def test_index_pagination(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.url + '?page=1')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['page_obj']), 2)
        
    def test_index_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/authentication/login'))
        
class AddIncomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@prueba.com', password='password123')
        self.source = Source.objects.create(name='Salary')
        self.url = reverse('add-income')
        self.preference = UserPreference.objects.create(user=self.user, currency='USD')
        
    def test_add_income_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, '/authentication/login?next=' + self.url)
        
    def test_add_income_view_get(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'income/add_income.html')
        
    def test_add_income_post_successful(self):
        self.client.login(username='testuser', password='password123')
        data = {
            'amount': 1000,
            'description': 'Salary for March',
            'income_date': '2024-03-30',
            'source': self.source.name
        }
        response = self.client.post(self.url, data)
        self.assertRedirects(response, reverse('income'))
        self.assertTrue(UserIncome.objects.filter(description='Salary for March').exists())
        
    def test_add_income_post_missing_amount(self):
        self.client.login(username='testuser', password='password123')
        data = {
            'amount': '',
            'description': 'Salary for March',
            'income_date': '2024-03-30',
            'source': self.source.name
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Amount is required')
        self.assertFalse(UserIncome.objects.filter(description='Freelance work').exists())
    
    def test_add_income_post_missing_amount(self):
        self.client.login(username='testuser', password='password123')
        data = {
            'amount': '500',
            'description': '',
            'income_date': '2024-03-30',
            'source': self.source.name
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Description is required')
        self.assertFalse(UserIncome.objects.filter(amount=500).exists())
        
    def test_add_income_post_missing_amount(self):
        self.client.login(username='testuser', password='password123')
        data = {
            'amount': '500',
            'description': 'Bonus',
            'income_date': '',
            'source': self.source.name
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Date is required')
        self.assertFalse(UserIncome.objects.filter(description='Bonus').exists())
        
class IncomeEditViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@prueba.com', password='password123')
        self.source = Source.objects.create(name='Salary')
        self.preference = UserPreference.objects.create(user=self.user, currency='USD')
        self.income = UserIncome.objects.create(
            owner = self.user,
            amount = 1000.00,
            date = date.today(),
            source = self.source.name,
            description = 'Test income'
        )
        self.url = reverse('income-edit', args=[self.income.id])
        
    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, '/authentication/login?next=' + self.url)
        
    def test_get_income_edit_authenticated_user(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'income/edit_income.html')
        
    def test_post_income_edit_success(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.url, {
            'amount': '1500.00',
            'description': 'Updated income',
            'income_date': date.today().strftime('%Y-%m-%d'),
            'source': self.source.name
        })
        self.income.refresh_from_db()
        self.assertEqual(self.income.amount, 1500.00)
        self.assertEqual(self.income.description, 'Updated income')
        self.assertRedirects(response, reverse('income'))
        
    def test_post_income_edit_missing_amount(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.url, {
            'amount': '',
            'description': 'Updated income',
            'income_date': date.today().strftime('%Y-%m-%d'),
            'source': self.source.name
        })
        self.assertContains(response, 'Amount is required')
        
    def test_post_income_edit_missing_description(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.url, {
            'amount': '1500.00',
            'description': '',
            'income_date': date.today().strftime('%Y-%m-%d'),
            'source': self.source.name
        })
        self.assertContains(response, 'Description is required')
        
    def test_post_income_edit_missing_description(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.url, {
            'amount': '1500.00',
            'description': 'Updated income',
            'income_date': '',
            'source': self.source.name
        })
        self.assertContains(response, 'Date is required')
        
class DeleteIncomeViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@prueba.com', password='password123')
        self.preference = UserPreference.objects.create(user=self.user, currency='USD')
        self.income = UserIncome.objects.create(
            owner = self.user,
            amount = 1000.00,
            date = date.today(),
            source = 'Freelancing',
            description = 'Test income'
        )
        self.url = reverse('income-delete', args=[self.income.id])
        
    def test_delete_income_authenticated_user(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.url)
        self.assertRedirects(response, reverse('income'))
        self.assertFalse(UserIncome.objects.filter(id=self.income.id).exists())
        
    def test_delete_income_unauthenticated_user_redirect(self):
        response = self.client.post(self.url)
        self.assertRedirects(response, f'/authentication/login?next={self.url}')
        self.assertTrue(UserIncome.objects.filter(id=self.income.id).exists())
        
class IncomeCategorySummaryViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@prueba.com', password='password123')
        self.url = reverse('income_category_summary')
        
        UserIncome.objects.create(
            owner = self.user,
            amount = 100,
            date = datetime.date.today(),
            description = 'Ingreso 1',
            source = 'Trabajo'
        )
        
        UserIncome.objects.create(
            owner = self.user,
            amount = 200,
            date = datetime.date.today(),
            description = 'Ingreso 2',
            source = 'Freelance'
        )
                
        UserIncome.objects.create(
            owner = self.user,
            amount = 50,
            date = datetime.date.today(),
            description = 'Ingreso 3',
            source = 'Trabajo'
        )
        
    def test_income_category_summary_authenticated_user(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('income_category_data', data)
        self.assertEqual(data['income_category_data']['Trabajo'], 150)
        self.assertEqual(data['income_category_data']['Freelance'], 200)
        
    def test_income_category_summary_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/authentication/login?next={self.url}')
        
class StatsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@prueba.com', password='password123')
        self.url = reverse('stats_income')
        
    def test_stats_view_authenticated_user(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'income/stats.html')
        
    def test_stats_view_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f'/authentication/login?next={self.url}')
        