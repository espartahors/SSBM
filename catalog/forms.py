# catalog/forms.py
from django import forms
from .models import Category, Product, Attribute, ProductTemplate


class ProductFilterForm(forms.Form):
    """Form for filtering products by various criteria"""
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search products...'}),
        label=''
    )
    
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    template = forms.ModelChoiceField(
        queryset=ProductTemplate.objects.all(),
        required=False,
        empty_label="All Templates",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min'}),
        label='Price Range'
    )
    
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max'})
    )
    
    in_stock = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='In Stock Only'
    )
    
    sort_by = forms.ChoiceField(
        choices=[
            ('name', 'Name (A-Z)'),
            ('-name', 'Name (Z-A)'),
            ('price', 'Price (Low to High)'),
            ('-price', 'Price (High to Low)'),
            ('-created_at', 'Newest First')
        ],
        required=False,
        initial='name',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        # Get available attributes for filtering
        available_attributes = kwargs.pop('available_attributes', None)
        super().__init__(*args, **kwargs)
        
        # Add dynamic attribute fields based on current products
        if available_attributes:
            for attr in available_attributes:
                field_name = f'attr_{attr.slug}'
                
                if attr.attr_type == 'text' or attr.attr_type == 'choice':
                    if attr.choices_list:
                        choices = [('', 'Any')] + [(choice.strip(), choice.strip()) for choice in attr.choices_list.split(',')]
                        self.fields[field_name] = forms.ChoiceField(
                            choices=choices,
                            required=False,
                            label=attr.name,
                            widget=forms.Select(attrs={'class': 'form-select'})
                        )
                    else:
                        self.fields[field_name] = forms.CharField(
                            required=False,
                            label=attr.name,
                            widget=forms.TextInput(attrs={'class': 'form-control'})
                        )
                        
                elif attr.attr_type == 'number':
                    self.fields[f'min_{field_name}'] = forms.DecimalField(
                        required=False,
                        label=f'Min {attr.name}',
                        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Min'})
                    )
                    self.fields[f'max_{field_name}'] = forms.DecimalField(
                        required=False,
                        label=f'Max {attr.name}',
                        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Max'})
                    )
                    
                elif attr.attr_type == 'boolean':
                    self.fields[field_name] = forms.BooleanField(
                        required=False,
                        label=attr.name,
                        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                    )


class ProductToEquipmentForm(forms.Form):
    """Form for associating products with equipment"""
    equipment_id = forms.IntegerField(widget=forms.HiddenInput())
    product_ids = forms.MultipleChoiceField(
        choices=[],  # Will be populated dynamically
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'list-unstyled'})
    )
    
    def __init__(self, *args, **kwargs):
        equipment = kwargs.pop('equipment', None)
        super().__init__(*args, **kwargs)
        
        if equipment:
            self.fields['equipment_id'].initial = equipment.id
            
            # Get all products
            products = Product.objects.all().order_by('category__name', 'name')
            
            # Set choices and initial values
            self.fields['product_ids'].choices = [(str(p.id), f"{p.name} ({p.sku})") for p in products]
            self.fields['product_ids'].initial = [str(p.id) for p in equipment.catalog_products.all()]