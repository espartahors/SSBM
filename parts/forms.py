# parts/forms.py

from django import forms
from .models import Part, Document, MarkedPart

class PartForm(forms.ModelForm):
    """Form for creating and updating parts"""
    class Meta:
        model = Part
        fields = ['part_id', 'name', 'level', 'info', 'parent']
        widgets = {
            'part_id': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.NumberInput(attrs={'class': 'form-control'}),
            'info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'parent': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(PartForm, self).__init__(*args, **kwargs)
        
        # Make parent field optional
        self.fields['parent'].required = False
        
        # Exclude the current part from parent options if editing
        if self.instance.pk:
            self.fields['parent'].queryset = Part.objects.exclude(pk=self.instance.pk)
            
            # Don't allow selecting any children as parent (would create a cycle)
            children = self.instance.get_all_children()
            if children:
                self.fields['parent'].queryset = self.fields['parent'].queryset.exclude(
                    pk__in=[child.pk for child in children]
                )
        
        # Sort parent options by ID for easier selection
        self.fields['parent'].queryset = self.fields['parent'].queryset.order_by('part_id')

class DocumentForm(forms.ModelForm):
    """Form for uploading documents"""
    class Meta:
        model = Document
        fields = ['part', 'title', 'description', 'document_type', 'file']
        widgets = {
            'part': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

class DocumentUpdateForm(forms.ModelForm):
    """Form for updating document metadata (without changing the file)"""
    class Meta:
        model = Document
        fields = ['part', 'title', 'description', 'document_type']
        widgets = {
            'part': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
        }

class MarkedPartForm(forms.ModelForm):
    """Form for marking parts"""
    class Meta:
        model = MarkedPart
        fields = ['part', 'note']
        widgets = {
            'part': forms.HiddenInput(),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional note'}),
        }

class ImportCSVForm(forms.Form):
    """Form for importing CSV data"""
    csv_file = forms.FileField(
        label='Select a CSV file',
        help_text='The file should have columns: ID, Name, Level, Info, DocRef',
        widget=forms.FileInput(attrs={'class': 'form-control-file'})
    )
    
    UPDATE_CHOICES = [
        ('add_only', 'Add new parts only'),
        ('update_existing', 'Update existing parts'),
        ('replace_all', 'Replace all parts (caution: deletes existing parts)'),
    ]
    
    update_mode = forms.ChoiceField(
        label='Update Mode',
        choices=UPDATE_CHOICES,
        initial='update_existing',
        widget=forms.RadioSelect
    )
    
    skip_errors = forms.BooleanField(
        label='Skip errors and continue importing',
        required=False,
        initial=True
    )

class PartSearchForm(forms.Form):
    """Form for searching parts"""
    search_term = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by ID, name, or info...'
        })
    )
    
    level = forms.IntegerField(
        required=False, 
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Level'
        })
    )
    
    has_documents = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    is_marked = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )