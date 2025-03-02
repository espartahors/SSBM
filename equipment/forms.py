# equipment/forms.py
from django import forms
from .models import Equipment, EquipmentCategory
from parts.models import Part

class EquipmentCategoryForm(forms.ModelForm):
    """Form for creating and updating equipment categories"""
    class Meta:
        model = EquipmentCategory
        fields = ['name', 'code', 'description', 'parent']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'parent': forms.Select(attrs={'class': 'form-control select2'}),
        }

class EquipmentForm(forms.ModelForm):
    """Form for creating and editing equipment items"""
    class Meta:
        model = Equipment
        fields = ['code', 'name', 'description', 'level', 'parent', 
                  'fabricant', 'doc_reference', 'status']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'parent': forms.Select(attrs={'class': 'form-select select2'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Prevent selecting self as parent
        if self.instance.pk:
            self.fields['parent'].queryset = Equipment.objects.exclude(pk=self.instance.pk)
            
        # Set help text for code field
        if self.instance.parent:
            prefix = self.instance.parent.full_code
            self.fields['code'].help_text = f"Parent code prefix: {prefix}-"
        else:
            self.fields['code'].help_text = "Top level code (no parent)"
class EquipmentCSVImportForm(forms.Form):
    """Form for importing equipment hierarchy from CSV"""
    csv_file = forms.FileField(
        label='Select a CSV file',
        help_text='Max. 5 megabytes',
        widget=forms.FileInput(attrs={'accept': '.csv'})
    )
    update_existing = forms.BooleanField(
        required=False, 
        initial=True,
        help_text='Update existing equipment if code already exists'
    )
    clear_existing = forms.BooleanField(
        required=False,
        initial=False,
        help_text='WARNING: Clear all existing equipment before import'
    )