# equipment/api_views.py

import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Equipment, EquipmentCategory
from users.decorators import can_edit_parts
from users.models import UserActivity

@login_required
def get_equipment_tree_data(request):
    """API endpoint for getting the root level equipment data for the tree view"""
    try:
        # Get top-level equipment (no parent)
        root_equipment = Equipment.objects.filter(parent__isnull=True).order_by('position', 'name')
        
        # Format data for jstree
        tree_data = []
        for item in root_equipment:
            # Check if this item has children
            has_children = Equipment.objects.filter(parent=item).exists()
            
            tree_data.append({
                'id': f'equipment_{item.id}',
                'text': f'{item.name} <span class="equipment-code">{item.code}</span>',
                'type': item.status,  # Use status as the node type
                'children': has_children,
                'data': {
                    'status': item.status,
                    'category': str(item.category.id) if item.category else '',
                    'location': item.location or ''
                }
            })
        
        return JsonResponse(tree_data, safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def get_equipment_children(request):
    """API endpoint for getting the children of a specific equipment node"""
    try:
        node_id = request.GET.get('node', '').replace('equipment_', '')
        
        if not node_id:
            return JsonResponse({'error': 'No node ID provided'}, status=400)
        
        # Get the parent equipment
        parent = Equipment.objects.get(id=node_id)
        
        # Get children of this equipment
        children = Equipment.objects.filter(parent=parent).order_by('position', 'name')
        
        # Format data for jstree
        children_data = []
        for item in children:
            # Check if this item has its own children
            has_children = Equipment.objects.filter(parent=item).exists()
            
            children_data.append({
                'id': f'equipment_{item.id}',
                'text': f'{item.name} <span class="equipment-code">{item.code}</span>',
                'type': item.status,  # Use status as the node type
                'children': has_children,
                'data': {
                    'status': item.status,
                    'category': str(item.category.id) if item.category else '',
                    'location': item.location or ''
                }
            })
        
        return JsonResponse(children_data, safe=False)
    except Equipment.DoesNotExist:
        return JsonResponse({'error': 'Equipment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
@can_edit_parts
@require_POST
def update_equipment_position(request):
    """API endpoint for updating equipment position in the hierarchy"""
    try:
        # Parse JSON body
        data = json.loads(request.body)
        equipment_id = data.get('id')
        parent_id = data.get('parent_id')
        position = data.get('position', 0)
        
        # Get the equipment to update
        equipment = Equipment.objects.get(id=equipment_id)
        
        # Update parent if provided
        if parent_id:
            # Check that we're not creating a circular reference
            parent = Equipment.objects.get(id=parent_id)
            
            # Check that parent is not a descendant of this equipment
            current_parent = parent
            while current_parent:
                if current_parent.id == equipment.id:
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Cannot set a descendant as parent (circular reference)'
                    }, status=400)
                current_parent = current_parent.parent
                
            equipment.parent = parent
        else:
            equipment.parent = None
        
        # Update position
        equipment.position = position
        equipment.save()
        
        # Log the activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='equipment_position_update',
            description=f'Updated position of equipment {equipment.code} ({equipment.name})',
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return JsonResponse({'status': 'success'})
    
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