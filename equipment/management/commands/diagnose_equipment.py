# Save this as equipment/management/commands/diagnose_equipment.py
from django.core.management.base import BaseCommand
from equipment.models import Equipment, EquipmentCategory
import json

class Command(BaseCommand):
    help = 'Diagnose equipment hierarchy data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting equipment hierarchy diagnosis'))
        
        # Check if there are any equipment items
        equipment_count = Equipment.objects.count()
        self.stdout.write(f'Total equipment items: {equipment_count}')
        
        if equipment_count == 0:
            self.stdout.write(self.style.WARNING('No equipment found in the database.'))
            return
        
        # Check categories
        category_count = EquipmentCategory.objects.count()
        self.stdout.write(f'Total equipment categories: {category_count}')
        
        # Check parent-child relationships
        root_equipment = Equipment.objects.filter(parent__isnull=True).count()
        self.stdout.write(f'Root equipment (no parent): {root_equipment}')
        
        # Check for circular references
        self.stdout.write('Checking for circular references...')
        circular_refs = self._check_circular_references()
        if circular_refs:
            self.stdout.write(self.style.ERROR(f'Found {len(circular_refs)} circular references:'))
            for item_id, path in circular_refs:
                self.stdout.write(self.style.ERROR(f'  - Equipment ID {item_id}: {" -> ".join(path)}'))
        else:
            self.stdout.write(self.style.SUCCESS('No circular references found.'))
        
        # Sample of equipment tree data format
        self.stdout.write('\nSample of equipment tree data format:')
        tree_sample = self._get_tree_sample()
        self.stdout.write(json.dumps(tree_sample, indent=2))
        
        self.stdout.write(self.style.SUCCESS('Diagnosis complete'))
    
    def _check_circular_references(self):
        """Check for circular references in the equipment hierarchy"""
        circular_refs = []
        for equipment in Equipment.objects.all():
            visited = {}
            path = []
            current = equipment
            
            while current and current.parent:
                path.append(f"{current.id}:{current.name}")
                
                if current.parent.id in visited:
                    # Circular reference found
                    circular_refs.append((current.id, path))
                    break
                
                visited[current.id] = True
                current = current.parent
        
        return circular_refs
    
    def _get_tree_sample(self):
        """Get a sample of the equipment tree data format"""
        equipment_items = Equipment.objects.all()[:10]  # Get first 10 items
        
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
        
        return tree_data