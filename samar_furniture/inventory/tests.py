from django.test import TestCase
from .models import InventoryItem
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from .forms import InventoryItemForm

# Create your tests here.

class InventoryItemModelTest(TestCase):
    def test_create_inventory_item(self):
        item = InventoryItem.objects.create(
            name='Test Item',
            description='A test item',
            quantity=10,
            price=99.99,
            low_stock_threshold=2
        )
        self.assertEqual(item.name, 'Test Item')
        self.assertEqual(item.quantity, 10)
        self.assertEqual(item.price, 99.99)

class InventoryViewPermissionTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.admin = User.objects.create_user(email='admin@test.com', password='pass', role='admin')
        self.owner = User.objects.create_user(email='owner@test.com', password='pass', role='shop_owner')
        self.support = User.objects.create_user(email='support@test.com', password='pass', role='it_support')
        self.item = InventoryItem.objects.create(name='Item1', quantity=5, price=10, low_stock_threshold=3)

    def test_inventory_list_access(self):
        self.client.login(email='support@test.com', password='pass')
        response = self.client.get(reverse('inventory_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Item1')

    def test_add_permission(self):
        self.client.login(email='support@test.com', password='pass')
        response = self.client.get(reverse('inventory_add'))
        self.assertRedirects(response, reverse('inventory_list'))
        self.client.login(email='admin@test.com', password='pass')
        response = self.client.get(reverse('inventory_add'))
        self.assertEqual(response.status_code, 200)

    def test_add_inventory_item(self):
        self.client.login(email='admin@test.com', password='pass')
        response = self.client.post(reverse('inventory_add'), {
            'name': 'NewItem',
            'quantity': 2,
            'price': 5.5,
            'low_stock_threshold': 1
        })
        self.assertRedirects(response, reverse('inventory_list'))
        self.assertTrue(InventoryItem.objects.filter(name='NewItem').exists())

    def test_edit_permission(self):
        self.client.login(email='support@test.com', password='pass')
        response = self.client.get(reverse('inventory_edit', args=[self.item.pk]))
        self.assertRedirects(response, reverse('inventory_list'))
        self.client.login(email='owner@test.com', password='pass')
        response = self.client.get(reverse('inventory_edit', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)

    def test_delete_permission(self):
        self.client.login(email='support@test.com', password='pass')
        response = self.client.get(reverse('inventory_delete', args=[self.item.pk]))
        self.assertRedirects(response, reverse('inventory_list'))
        self.client.login(email='admin@test.com', password='pass')
        response = self.client.post(reverse('inventory_delete', args=[self.item.pk]))
        self.assertRedirects(response, reverse('inventory_list'))
        self.assertFalse(InventoryItem.objects.filter(pk=self.item.pk).exists())

class InventoryItemFormTest(TestCase):
    def test_valid_form(self):
        form_data = {
            'name': 'FormItem',
            'quantity': 3,
            'price': 12.5,
            'low_stock_threshold': 2
        }
        form = InventoryItemForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        form_data = {
            'name': '',  # Name required
            'quantity': -1,  # Invalid
            'price': -5,  # Invalid
            'low_stock_threshold': -2
        }
        form = InventoryItemForm(data=form_data)
        self.assertFalse(form.is_valid())
