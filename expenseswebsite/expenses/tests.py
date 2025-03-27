from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.utils.timezone import now
from django.urls import reverse
import json
from expenses.models import Expense, Category
from userpreferences.models import UserPreference
from datetime import timedelta
from django.contrib.messages import get_messages
import datetime

# Create your tests here.

class ExpenseModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.category = Category.objects.create(name='Food')
        self.expense = Expense.objects.create(
            amount = 50.75,
            date = now().date(),
            description = 'Dinner at a restaurant',
            owner = self.user,
            category = self.category.name
        )
        
    def test_expense_creation(self):
        self.assertEqual(self.expense.amount, 50.75)
        self.assertEqual(self.expense.description, 'Dinner at a restaurant')
        self.assertEqual(self.expense.owner, self.user)
        self.assertEqual(self.expense.category, 'Food')
        
    def test_expense_str_respresentation(self):
        self.assertEqual(str(self.expense), 'Food')
        
    def test_expense_ordering(self):
        expense2 = Expense.objects.create(
            amount = 30.00,
            date = now().date(),
            description = 'Groceries',
            owner = self.user,
            category = 'Shopping'
        )
        expenses = Expense.objects.all()
        self.assertEqual(expenses.first(), self.expense)
        
class CategoryModelTest(TestCase):
    def test_category_creation(self):
        category = Category.objects.create(name="Transport")
        self.assertEqual(category.name, 'Transport')
        
    def test_category_str_representation(self): 
        category = Category.objects.create(name="Entertainment")
        self.assertEqual(str(category), "Entertainment")
class SearchExpenseTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')
        
        self.client.login(username='testuser', password='password123')
        
        self.category = Category.objects.create(name='Food')
        
        self.expense1 = Expense.objects.create(
            amount = 50.75,
            date = now().date(),
            description = "Dinner at a restaurant",
            owner = self.user,
            category = "Food"
        )
        
        self.expense2 = Expense.objects.create(
            amount = 20.00,
            date = now().date(),
            description = "Lunch at work",
            owner = self.user,
            category = "Work"
        )
                
        self.expense3 = Expense.objects.create(
            amount = 15.00,
            date = now().date(),
            description = "Taxi ride",
            owner = self.user,
            category = "Transport"
        )
        
        self.url = '/search-expenses'
        
    def test_search_by_amount(self):
        response = self.client.post(self.url, json.dumps({'searchText': '50'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['description'], 'Dinner at a restaurant')
        
    def test_search_by_date(self):
        response = self.client.post(self.url, json.dumps({'searchText': str(now().date())}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)
        
    def test_search_by_description(self):
        response = self.client.post(self.url, json.dumps({'searchText': 'Taxi'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['category'], 'Transport')
        
    def test_search_by_category(self):
        response = self.client.post(self.url, json.dumps({'searchText': 'Food'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['description'], 'Dinner at a restaurant')
        
    def test_search_no_results(self):
        response = self.client.post(self.url, json.dumps({'searchText': 'NonExistent'}), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 0)
        
class IndexViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')
        
        self.category = Category.objects.create(name='Food')
        
        self.user_preference = UserPreference.objects.create(user=self.user, currency='USD')
        
        self.expense1 = Expense.objects.create(
            amount = 50.75,
            date = now().date(),
            description = "Dinner at a restaurant",
            owner = self.user,
            category = "Food"
        )
        
        self.expense2 = Expense.objects.create(
            amount = 20.00,
            date = now().date(),
            description = "Lunch at work",
            owner = self.user,
            category = "Work"
        )
                
        self.expense3 = Expense.objects.create(
            amount = 15.00,
            date = now().date(),
            description = "Taxi ride",
            owner = self.user,
            category = "Transport"
        )
        
        self.url = '/'
    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith('/authentication/login'))
        
    def test_index_view_loads_for_logged_in_user(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.url + '?page=1')
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'expenses/index.html')
        
    def test_user_expenses_are_displayed(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.url)
        self.assertContains(response, "Dinner at a restaurant")
        self.assertContains(response, "Lunch at work")
        
    def test_pagination_works(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.url + '?page=1')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('page_obj' in response.context)
        self.assertEqual(len(response.context['page_obj']), 2)
        
    def test_currency_is_displayed(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.url)
        self.assertContains(response, 'USD')
        
class AddExpenseViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.category = Category.objects.create(name='Food')
        self.url = '/add-expense'
        
    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, '/authentication/login?next=' + self.url)
        
    def test_get_add_expense_page(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'expenses/add_expense.html')
        
    def test_post_valid_expense(self):
        self.client.login(username='testuser', password='password123')
        data = {
            'amount': '100.50',
            'description': 'Groceries',
            'expense_date': now().date().isoformat(),
            'category': self.category.name
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Expense.objects.filter(description='Groceries', owner = self.user).exists())
        
    def test_post_missing_amount(self):
        self.client.login(username='testuser', password='password123')
        data = {
            'amount': '',
            'description': 'Dinner',
            'expense_date': now().date().isoformat(),
            'category': self.category.name
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Amount is required')
        self.assertFalse(Expense.objects.filter(description='Dinner').exists())
        
    def test_post_missing_description(self):
        self.client.login(username='testuser', password='password123')
        data = {
            'amount': '50',
            'description': '',
            'expense_date': now().date().isoformat(),
            'category': self.category.name
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Description is required')

    def test_post_missing_date(self):
        self.client.login(username='testuser', password='password123')
        data = {
            'amount': '50',
            'description': 'Bus tiquet',
            'expense_date': '',
            'category': self.category.name
        }

class ExpenseEditViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.category = Category.objects.create(name='Food')
        self.expense = Expense.objects.create(
            amount = 50.75,
            date = now().date(),
            description = 'Dinner at a restaurant',
            owner = self.user,
            category = self.category.name
        )
        self.url = f'/edit-expense/{self.expense.id}'
        UserPreference.objects.create(user=self.user, currency='USD')
    
    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.url)
        self.assertRedirects(response, '/authentication/login?next=' + self.url)
        
    def test_edit_expense_get(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'expenses/edit-expense.html')
        self.assertContains(response, 'Dinner at a restaurant')
        
    def test_edit_expense_post_valid(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.url,{
            'amount': 100.00,
            'description': 'Updated expense',
            'expense_date': now().date(),
            'category': 'Food'
        })
        self.expense.refresh_from_db()
        self.assertEqual(self.expense.amount, 100.00)
        self.assertEqual(self.expense.description, 'Updated expense')
        self.assertRedirects(response, '/')
        
    def test_edit_expense_post_missing_fields(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.url,{
            'amount': '',
            'description': 'Description',
            'expense_date': now().date(),
            'category': 'Food'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'expenses/edit-expense.html')
        self.assertContains(response, 'Amount is required')
        
class DeleteExpenseViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.category = Category.objects.create(name='Food')
        self.expense = Expense.objects.create(
            amount = 100.00,
            date = "2024-03-01",
            description = 'Groceries',
            owner = self.user,
            category = self.category.name
        )
        self.delete_url = reverse('expense-delete', args=[self.expense.id])
        
    def test_delete_expense_authenticated_user(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(self.delete_url)
        
        self.assertFalse(Expense.objects.filter(id=self.expense.id).exists())
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('expenses')))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Expense removed' in str(m) for m in messages))
        
    def test_delete_expense_unaunthenticated_user(self):
        self.client.logout()
        response = self.client.post(self.delete_url)
        self.assertTrue(Expense.objects.filter(id=self.expense.id).exists())
        expeted_url = reverse('login') + f'?next={self.delete_url}'
        self.assertRedirects(response, expeted_url)
        
class ExpenseCategorySummaryViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.client.login(username='testuser', password='password123')
        self.category_food = Category.objects.create(name='Food')
        self.category_travel = Category.objects.create(name='Travel')
        
        self.six_months_ago = now().date() - datetime.timedelta(days=30 * 6)
        self.recent_expense = Expense.objects.create(
            owner = self.user,
            amount = 100.00,
            date = self.six_months_ago + datetime.timedelta(days=10),
            category = self.category_food.name,
            description = 'Groceries'
        )
        self.old_expense = Expense.objects.create(
            owner = self.user,
            amount = 200.00,
            date = self.six_months_ago - datetime.timedelta(days=1),
            category = self.category_travel.name,
            description = 'Flight ticket'
        )
        
        self.url = reverse('expense_category_summary')
    
    def test_expense_summary_authenticated_user(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        
        self.assertIn('Food', data['expense_category_data'])
        self.assertNotIn("Travel", data["expense_category_data"])
        self.assertEqual(data['expense_category_data']['Food'], 100.0)
        
class StatsViewTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.url = reverse('stats')
        
    def test_stats_view_authenticated_user(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'expenses/stats.html')
        
    def test_stats_view_unauthenticated_user(self):
        response = self.client.get(self.url)
        self.assertNotEqual(response.status_code, 200)
        self.assertRedirects(response, f'/authentication/login?next={self.url}')