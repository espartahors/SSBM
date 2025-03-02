# equipment/views.py
import csv
import io
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.views.decorators.http import require_POST


from users.models import UserActivity
from users.decorators import can_add_parts, can_edit_parts, can_delete_parts, can_upload_csv
from .models import Equipment, EquipmentCategory
from .forms import EquipmentForm, EquipmentCategoryForm, EquipmentCSVImportForm

# Equipment CRUD views
class EquipmentListView(ListView):
    model = Equipment
    template_name = 'equipment/equipment_list.html'
    context_object_name = 'equipment_list'

class EquipmentDetailView(DetailView):
    model = Equipment
    template_name = 'equipment/equipment_detail.html'
    context_object_name = 'equipment'

@method_decorator(can_add_parts, name='dispatch')
class EquipmentCreateView(CreateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = 'equipment/equipment_form.html'

@login_required
def test_equipment_tree_view(request):
    """Simplified test view for the equipment tree"""
    return render(request, 'equipment/simple-tree-template.html')

@method_decorator(can_edit_parts, name='dispatch')
class EquipmentUpdateView(UpdateView):
    model = Equipment
    form_class = EquipmentForm
    template_name = 'equipment/equipment_form.html'

@method_decorator(can_delete_parts, name='dispatch')
class EquipmentDeleteView(DeleteView):
    model = Equipment
    template_name = 'equipment/equipment_confirm_delete.html'
    success_url = reverse_lazy('equipment-list')

# Equipment Tree View
@login_required
def equipment_tree_view(request):
    categories = EquipmentCategory.objects.all()
    return render(request, 'equipment/equipment_tree.html', {
        'categories': categories,
    })

@login_required
def equipment_level_tree_view(request):
    """Render the equipment tree with data based on level hierarchy"""
    # Get all equipment items
    equipment_items = Equipment.objects.all().order_by('level', 'position', 'code')
    
    # Prepare data for jstree
    tree_data = []
    for item in equipment_items:
        # Determine parent ID for tree structure
        parent_id = f'equipment_{item.parent_id}' if item.parent else '#'
        
        # Create node data with additional information
        node = {
            'id': f'equipment_{item.id}',
            'text': f'<span class="equipment-level">{item.level}</span> {item.name} <span class="equipment-code">{item.full_code}</span>',
            'parent': parent_id,
            'type': item.status,
            'data': {
                'level': item.level,
                'code': item.code,
                'full_code': item.full_code,
                'baseName': f'<span class="equipment-level">{item.level}</span> {item.name} <span class="equipment-code">{item.full_code}</span>',
                'fabricant': item.fabricant,
                'description': item.description,
                'status': item.status
            }
        }
        tree_data.append(node)
    
    # Convert to JSON for the template
    tree_data_json = json.dumps(tree_data)
    
    return render(request, 'equipment/level_based_tree.html', {
        'tree_data_json': tree_data_json,
        'equipment_count': equipment_items.count()
    })

# AJAX endpoints for tree operations
@login_required
@can_edit_parts
@require_POST
def update_equipment_position(request):
    """API endpoint for updating equipment position and parent"""
    try:
        # Parse the request body
        data = json.loads(request.body)
        equipment_id = data.get('id')
        parent_id = data.get('parent_id')
        position = int(data.get('position', 0))
        
        # Get the equipment to update
        equipment = Equipment.objects.get(id=equipment_id)
        
        # Check for circular reference if parent is provided
        if parent_id:
            # Get the new parent
            parent = Equipment.objects.get(id=parent_id)
            
            # Check that this parent is not a descendant of the equipment
            current = parent
            while current:
                if current.id == equipment.id:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Cannot create circular reference'
                    }, status=400)
                current = current.parent
            
            # Update parent if different
            if equipment.parent_id != parent.id:
                equipment.parent = parent
                # Update level based on parent's level
                equipment.level = parent.level + 1
        else:
            # If no parent, set as top level
            equipment.parent = None
            equipment.level = 1
        
        # Update position
        equipment.position = position
        equipment.save()
        
        # Update all children's levels recursively
        update_children_levels(equipment)
        
        return JsonResponse({
            'status': 'success',
            'message': 'Equipment position updated successfully'
        })
    
    except Equipment.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Equipment not found'
        }, status=404)
    
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

# NEW CSV IMPORT
@login_required
@can_upload_csv
def import_equipment_level_csv(request):
    """Import equipment hierarchy from CSV using level-based structuring"""
    if request.method == 'POST':
        form = EquipmentCSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            update_existing = form.cleaned_data['update_existing']
            clear_existing = form.cleaned_data.get('clear_existing', False)
            
            # Clear existing data if requested
            if clear_existing:
                Equipment.objects.all().delete()
                messages.success(request, "All existing equipment data has been cleared.")
            
            # Process CSV file
            try:
                decoded_file = csv_file.read().decode('utf-8')
                io_string = io.StringIO(decoded_file)
                reader = csv.DictReader(io_string)
                
                # Track items by level for building the hierarchy
                level_stack = {}  # Will store the latest item for each level
                created_count = 0
                updated_count = 0
                error_count = 0
                
                # Process each row in the CSV
                for row in reader:
                    # Extract basic fields
                    code = row.get('Code', '')
                    level = int(row.get('Level', 1))
                    name = row.get('Name', '')
                    fabricant = row.get('Fabricant', '')
                    description = row.get('Reference', '')
                    doc_reference = row.get('Doc Ref', '')
                    
                    if not code or not name:
                        error_count += 1
                        continue
                    
                    try:
                        # Determine parent based on level
                        parent = None
                        if level > 1 and level - 1 in level_stack:
                            parent = level_stack[level - 1]
                        
                        # Check if equipment with this code and parent already exists
                        try:
                            if parent:
                                equipment = Equipment.objects.get(code=code, parent=parent)
                                is_new = False
                            else:
                                equipment = Equipment.objects.get(code=code, parent__isnull=True)
                                is_new = False
                        except Equipment.DoesNotExist:
                            equipment = Equipment(code=code)
                            is_new = True
                        
                        if is_new or update_existing:
                            # Update equipment attributes
                            equipment.name = name
                            equipment.level = level
                            equipment.parent = parent
                            equipment.fabricant = fabricant
                            equipment.description = description
                            equipment.doc_reference = doc_reference
                            
                            # Calculate position based on order in CSV
                            equipment.position = Equipment.objects.filter(
                                level=level, 
                                parent=parent
                            ).count()
                            
                            equipment.save()
                            
                            # Update counts for reporting
                            if is_new:
                                created_count += 1
                            else:
                                updated_count += 1
                            
                            # Update level stack to track this item for child references
                            level_stack[level] = equipment
                            
                            # Clear any higher levels when we move to a new branch
                            for l in list(level_stack.keys()):
                                if l > level:
                                    del level_stack[l]
                    
                    except Exception as e:
                        error_count += 1
                        messages.error(request, f"Error processing row with code {code}: {str(e)}")
                
                # Log the activity
                UserActivity.objects.create(
                    user=request.user,
                    activity_type='csv_import',
                    description=f'Imported equipment hierarchy from CSV: {created_count} created, {updated_count} updated',
                    ip_address=request.META.get('REMOTE_ADDR')
                )
                
                messages.success(
                    request, 
                    f'Import complete: {created_count} created, {updated_count} updated, {error_count} errors.'
                )
                return redirect('equipment-tree')
            
            except Exception as e:
                messages.error(request, f"Error processing CSV file: {str(e)}")
    else:
        form = EquipmentCSVImportForm()
    
    return render(request, 'equipment/import_level_csv.html', {
        'form': form,
        'csv_columns': ['Code', 'Level', 'Name', 'Reference', 'Fabricant', 'Doc Ref'],
    })



# CSV Import/Export
@login_required
@can_add_parts
def import_equipment_csv(request):
    if request.method == 'POST':
        form = EquipmentCSVImportForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['csv_file']
            update_existing = form.cleaned_data['update_existing']
            
            # Process CSV file
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            created_count = 0
            updated_count = 0
            error_count = 0
            
            for row in reader:
                try:
                    code = row.get('code', '').strip()
                    if not code:
                        continue
                        
                    # Try to find existing equipment by code
                    equipment, created = Equipment.objects.get_or_create(
                        code=code,
                        defaults={
                            'name': row.get('name', ''),
                            'description': row.get('description', ''),
                            'status': row.get('status', 'active'),
                            'location': row.get('location', ''),
                        }
                    )
                    
                    if created:
                        created_count += 1
                    elif update_existing:
                        equipment.name = row.get('name', equipment.name)
                        equipment.description = row.get('description', equipment.description)
                        equipment.status = row.get('status', equipment.status)
                        equipment.location = row.get('location', equipment.location)
                        equipment.save()
                        updated_count += 1
                        
                    # Handle parent relationship
                    parent_code = row.get('parent_code', '').strip()
                    if parent_code:
                        try:
                            parent = Equipment.objects.get(code=parent_code)
                            equipment.parent = parent
                            equipment.save()
                        except Equipment.DoesNotExist:
                            pass
                            
                except Exception as e:
                    error_count += 1
                    
            messages.success(request, f'Import complete: {created_count} created, {updated_count} updated, {error_count} errors.')
            return redirect('equipment-list')
    else:
        form = EquipmentCSVImportForm()
        
    return render(request, 'equipment/import_csv.html', {'form': form})

@login_required
def export_equipment_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="equipment_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['code', 'name', 'description', 'status', 'location', 'parent_code', 'category_name'])
    
    for equipment in Equipment.objects.all():
        writer.writerow([
            equipment.code,
            equipment.name,
            equipment.description,
            equipment.status,
            equipment.location,
            equipment.parent.code if equipment.parent else '',
            equipment.category.name if equipment.category else ''
        ])
        
    return response


@login_required
def equipment_direct_tree_view(request):
    """
    Render the equipment tree with data directly injected into the template
    instead of loading via AJAX
    """
    # Get all equipment
    equipment_items = Equipment.objects.all().order_by('position', 'name')
    categories = EquipmentCategory.objects.all()
    
    # Prepare data for the tree
    tree_data = []
    
    for item in equipment_items:
        node = {
            'id': f'equipment_{item.id}',
            'text': f'{item.name} <span class="equipment-code">{item.code}</span>',
            'type': item.status,
            'parent': f'equipment_{item.parent_id}' if item.parent_id else '#',
            'data': {
                'status': item.status,
                'category': str(item.category.id) if item.category else '',
                'location': item.location or ''
            }
        }
        tree_data.append(node)
    
    # Convert to JSON for use in the template
    tree_data_json = json.dumps(tree_data)
    
    return render(request, 'equipment/equipment_direct_tree.html', {
        'tree_data_json': tree_data_json,
        'categories': categories,
    })

def update_children_levels(equipment):
    """Recursively update the level of all children based on parent's level"""
    children = Equipment.objects.filter(parent=equipment)
    
    for child in children:
        child.level = equipment.level + 1
        child.save()
        
        # Recursively update grandchildren
        update_children_levels(child)