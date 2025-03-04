# catalog/equipment_integration.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse

from equipment.models import Equipment
from catalog.models import Product
from catalog.forms import ProductToEquipmentForm
from users.models import UserActivity
from users.decorators import can_edit_parts

@login_required
@can_edit_parts
def manage_equipment_parts(request, equipment_id):
    """View to manage parts associated with equipment"""
    equipment = get_object_or_404(Equipment, id=equipment_id)
    
    if request.method == 'POST':
        form = ProductToEquipmentForm(request.POST, equipment=equipment)
        
        if form.is_valid():
            # Get selected product IDs
            selected_ids = form.cleaned_data['product_ids']
            
            # Clear existing relationships
            equipment.catalog_products.clear()
            
            # Add new relationships
            if selected_ids:
                products = Product.objects.filter(id__in=selected_ids)
                equipment.catalog_products.add(*products)
            
            # Log the activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='equipment_update',
                description=f'Updated parts for equipment {equipment.code} ({equipment.name})',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, f'Parts for {equipment.name} have been updated.')
            return redirect('equipment-detail', pk=equipment.id)
    else:
        form = ProductToEquipmentForm(equipment=equipment)
    
    # Get all products grouped by category for easier selection
    products_by_category = {}
    
    for product in Product.objects.all().select_related('category'):
        category_name = product.category.name
        if category_name not in products_by_category:
            products_by_category[category_name] = []
        
        products_by_category[category_name].append(product)
    
    # Sort categories
    sorted_categories = sorted(products_by_category.keys())
    
    return render(request, 'catalog/manage_equipment_parts.html', {
        'form': form,
        'equipment': equipment,
        'products_by_category': products_by_category,
        'sorted_categories': sorted_categories
    })

@login_required
@can_edit_parts
def ajax_add_part_to_equipment(request):
    """AJAX endpoint to quickly add a part to equipment"""
    if request.method == 'POST':
        try:
            product_id = request.POST.get('product_id')
            equipment_id = request.POST.get('equipment_id')
            
            if not product_id or not equipment_id:
                return JsonResponse({'status': 'error', 'message': 'Missing parameters'}, status=400)
            
            product = get_object_or_404(Product, id=product_id)
            equipment = get_object_or_404(Equipment, id=equipment_id)
            
            # Add the product to the equipment
            equipment.catalog_products.add(product)
            
            # Log the activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='equipment_update',
                description=f'Added part {product.sku} to equipment {equipment.code}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
            return JsonResponse({
                'status': 'success',
                'message': f'Added {product.name} to {equipment.name}'
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)