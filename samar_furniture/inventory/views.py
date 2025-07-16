from django.shortcuts import render, redirect, get_object_or_404
from .models import InventoryItem
from .forms import InventoryItemForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
import csv
from django.http import HttpResponse

def user_is_admin_or_owner(user):
    return user.is_authenticated and user.role in ['admin', 'shop_owner']

@login_required
def inventory_list(request):
    query = request.GET.get('q', '')
    low_stock = request.GET.get('low_stock', '')
    page_number = request.GET.get('page', 1)
    items = InventoryItem.objects.all()
    if query:
        items = items.filter(name__icontains=query)
    if low_stock == '1':
        items = items.filter(quantity__lte=models.F('low_stock_threshold'))
    paginator = Paginator(items, 10)  # 10 items per page
    page_obj = paginator.get_page(page_number)
    return render(request, 'inventory/inventory_list.html', {
        'items': page_obj.object_list,
        'page_obj': page_obj,
        'search_query': query,
        'low_stock': low_stock,
    })

@login_required
def inventory_add(request):
    if not user_is_admin_or_owner(request.user):
        messages.error(request, 'You do not have permission to add inventory items.')
        return redirect('inventory_list')
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item added successfully!')
            return redirect('inventory_list')
    else:
        form = InventoryItemForm()
    return render(request, 'inventory/inventory_form.html', {'form': form, 'action': 'Add'})

@login_required
def inventory_edit(request, pk):
    if not user_is_admin_or_owner(request.user):
        messages.error(request, 'You do not have permission to edit inventory items.')
        return redirect('inventory_list')
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Item updated successfully!')
            return redirect('inventory_list')
    else:
        form = InventoryItemForm(instance=item)
    return render(request, 'inventory/inventory_form.html', {'form': form, 'action': 'Edit'})

@login_required
def inventory_delete(request, pk):
    if not user_is_admin_or_owner(request.user):
        messages.error(request, 'You do not have permission to delete inventory items.')
        return redirect('inventory_list')
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deleted successfully!')
        return redirect('inventory_list')
    return render(request, 'inventory/inventory_confirm_delete.html', {'item': item})

@login_required
def inventory_export_csv(request):
    query = request.GET.get('q', '')
    low_stock = request.GET.get('low_stock', '')
    items = InventoryItem.objects.all()
    if query:
        items = items.filter(name__icontains=query)
    if low_stock == '1':
        items = items.filter(quantity__lte=models.F('low_stock_threshold'))
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="inventory.csv"'
    writer = csv.writer(response)
    writer.writerow(['Name', 'Description', 'Quantity', 'Price', 'Low Stock Threshold', 'Created At', 'Updated At'])
    for item in items:
        writer.writerow([
            item.name,
            item.description,
            item.quantity,
            item.price,
            item.low_stock_threshold,
            item.created_at,
            item.updated_at
        ])
    return response
