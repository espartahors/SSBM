# catalog/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count, Prefetch
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from .models import Category, Product, Attribute, ProductTemplate, TemplateAttribute
from .forms import ProductFilterForm
from users.decorators import can_add_parts, can_edit_parts, can_delete_parts

def catalog_home(request):
    """Home page for the catalog showing top categories"""
    categories = Category.objects.filter(parent=None)
    
    # Get featured products (can be customized based on your business logic)
    featured_products = Product.objects.filter(
        stock__gt=0
    ).prefetch_related('images').order_by('-created_at')[:4]
    
    # Get newest products
    new_products = Product.objects.all().prefetch_related('images').order_by('-created_at')[:4]
    
    return render(request, 'catalog/home.html', {
        'categories': categories,
        'featured_products': featured_products,
        'new_products': new_products
    })

class CategoryDetailView(DetailView):
    """Display a category and its products/subcategories"""
    model = Category
    template_name = 'catalog/category_detail.html'
    context_object_name = 'category'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object
        
        # Get subcategories
        context['subcategories'] = category.get_children()
        
        # Get all products in this category and its descendants
        all_categories = [category] + list(category.get_descendants())
        
        # Start with all products in these categories
        products = Product.objects.filter(category__in=all_categories)
        
        # Apply filters
        if self.request.GET:
            # Subcategory filter
            subcategory_slug = self.request.GET.get('subcategory')
            if subcategory_slug:
                subcategory = get_object_or_404(Category, slug=subcategory_slug)
                products = products.filter(category=subcategory)
            
            # Price filters
            min_price = self.request.GET.get('min_price')
            if min_price:
                try:
                    products = products.filter(price__gte=float(min_price))
                except ValueError:
                    pass
                    
            max_price = self.request.GET.get('max_price')
            if max_price:
                try:
                    products = products.filter(price__lte=float(max_price))
                except ValueError:
                    pass
            
            # Stock filter
            if self.request.GET.get('in_stock'):
                products = products.filter(stock__gt=0)
            
            # Sort options
            sort_param = self.request.GET.get('sort')
            if sort_param:
                products = products.order_by(sort_param)
            
            # Attribute filters - this gets complex
            for key, value in self.request.GET.items():
                if key.startswith('attr_') and value:
                    attr_slug = key.replace('attr_', '')
                    try:
                        attr = Attribute.objects.get(slug=attr_slug)
                        
                        # Filter based on attribute type
                        if attr.attr_type == 'text' or attr.attr_type == 'choice':
                            products = products.filter(
                                attributes__attribute=attr,
                                attributes__value_text=value
                            )
                        elif attr.attr_type == 'number':
                            try:
                                value_float = float(value)
                                products = products.filter(
                                    attributes__attribute=attr,
                                    attributes__value_number=value_float
                                )
                            except ValueError:
                                pass
                        elif attr.attr_type == 'boolean':
                            bool_value = value.lower() in ('true', 'yes', '1')
                            products = products.filter(
                                attributes__attribute=attr,
                                attributes__value_boolean=bool_value
                            )
                    except Attribute.DoesNotExist:
                        pass
                        
                # Handle min/max range for numeric attributes
                elif key.startswith('min_attr_') and value:
                    attr_slug = key.replace('min_attr_', '')
                    try:
                        attr = Attribute.objects.get(slug=attr_slug)
                        value_float = float(value)
                        products = products.filter(
                            attributes__attribute=attr,
                            attributes__value_number__gte=value_float
                        )
                    except (Attribute.DoesNotExist, ValueError):
                        pass
                        
                elif key.startswith('max_attr_') and value:
                    attr_slug = key.replace('max_attr_', '')
                    try:
                        attr = Attribute.objects.get(slug=attr_slug)
                        value_float = float(value)
                        products = products.filter(
                            attributes__attribute=attr,
                            attributes__value_number__lte=value_float
                        )
                    except (Attribute.DoesNotExist, ValueError):
                        pass
        
        # Always prefetch related data for performance
        products = products.prefetch_related(
            'images', 'attributes__attribute', 'category'
        ).distinct()
        
        context['products'] = products
        
        # Get all attributes used by products in this category for filters
        product_ids = products.values_list('id', flat=True)
        attr_ids = set()
        
        from django.db.models import Count
        used_attributes = Attribute.objects.filter(
            productattribute__product__in=product_ids
        ).annotate(
            product_count=Count('productattribute__product', distinct=True)
        ).filter(
            product_count__gt=1  # Only include attributes used by multiple products
        ).order_by('name')
        
        context['filter_attributes'] = used_attributes
        
        return context

class ProductDetailView(DetailView):
    """Display a product and its details"""
    model = Product
    template_name = 'catalog/product_detail.html'
    context_object_name = 'product'
    
    def get_object(self, queryset=None):
        """Allow lookup by either ID or SKU"""
        if queryset is None:
            queryset = self.get_queryset()
            
        pk = self.kwargs.get(self.pk_url_kwarg)
        
        if pk.isdigit():
            # Lookup by ID
            return get_object_or_404(queryset, pk=pk)
        else:
            # Lookup by SKU
            return get_object_or_404(queryset, sku=pk)
    
    def get_queryset(self):
        """Prefetch related data for performance"""
        return super().get_queryset().prefetch_related(
            'images', 
            'attributes__attribute', 
            'related_equipment',
            Prefetch('category', queryset=Category.objects.select_related('parent'))
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get similar products (same category excluding this one)
        similar_products = Product.objects.filter(
            category=self.object.category
        ).exclude(
            id=self.object.id
        ).prefetch_related('images')[:4]
        
        context['similar_products'] = similar_products
        
        return context

class ProductListView(ListView):
    """List products with filtering and search"""
    model = Product
    template_name = 'catalog/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        """Get products with search and filter"""
        queryset = Product.objects.all()
        
        # Search query
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) | 
                Q(sku__icontains=q) | 
                Q(description__icontains=q)
            )
        
        # Category filter
        category_slug = self.request.GET.get('category')
        if category_slug:
            try:
                category = Category.objects.get(slug=category_slug)
                # Include all descendants of the selected category
                categories = [category] + list(category.get_descendants())
                queryset = queryset.filter(category__in=categories)
            except Category.DoesNotExist:
                pass
        
        # Template filter
        template_slug = self.request.GET.get('template')
        if template_slug:
            queryset = queryset.filter(template__slug=template_slug)
        
        # Price filters
        min_price = self.request.GET.get('min_price')
        if min_price:
            try:
                queryset = queryset.filter(price__gte=float(min_price))
            except ValueError:
                pass
                
        max_price = self.request.GET.get('max_price')
        if max_price:
            try:
                queryset = queryset.filter(price__lte=float(max_price))
            except ValueError:
                pass
        
        # Stock filter
        if self.request.GET.get('in_stock'):
            queryset = queryset.filter(stock__gt=0)
        
        # Attribute filters - handle dynamically
        for key, value in self.request.GET.items():
            if key.startswith('attr_') and value:
                attr_slug = key.replace('attr_', '')
                try:
                    attr = Attribute.objects.get(slug=attr_slug)
                    
                    # Filter based on attribute type
                    if attr.attr_type == 'text' or attr.attr_type == 'choice':
                        queryset = queryset.filter(
                            attributes__attribute=attr,
                            attributes__value_text=value
                        )
                    elif attr.attr_type == 'number':
                        try:
                            value_float = float(value)
                            queryset = queryset.filter(
                                attributes__attribute=attr,
                                attributes__value_number=value_float
                            )
                        except ValueError:
                            pass
                    elif attr.attr_type == 'boolean':
                        bool_value = value.lower() in ('true', 'yes', '1')
                        queryset = queryset.filter(
                            attributes__attribute=attr,
                            attributes__value_boolean=bool_value
                        )
                except Attribute.DoesNotExist:
                    pass
                    
            # Handle min/max range for numeric attributes
            elif key.startswith('min_attr_') and value:
                attr_slug = key.replace('min_attr_', '')
                try:
                    attr = Attribute.objects.get(slug=attr_slug)
                    value_float = float(value)
                    queryset = queryset.filter(
                        attributes__attribute=attr,
                        attributes__value_number__gte=value_float
                    )
                except (Attribute.DoesNotExist, ValueError):
                    pass
                    
            elif key.startswith('max_attr_') and value:
                attr_slug = key.replace('max_attr_', '')
                try:
                    attr = Attribute.objects.get(slug=attr_slug)
                    value_float = float(value)
                    queryset = queryset.filter(
                        attributes__attribute=attr,
                        attributes__value_number__lte=value_float
                    )
                except (Attribute.DoesNotExist, ValueError):
                    pass
        
        # Sort options
        sort_param = self.request.GET.get('sort')
        if sort_param:
            queryset = queryset.order_by(sort_param)
        else:
            # Default sort by name
            queryset = queryset.order_by('name')
        
        # Always prefetch related data for performance
        return queryset.prefetch_related(
            'images', 'attributes__attribute', 'category'
        ).distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['templates'] = ProductTemplate.objects.all()
        
        # Get filterable attributes for the current product set
        product_ids = self.get_queryset().values_list('id', flat=True)
        
        # Find attributes that appear in multiple products
        from django.db.models import Count
        used_attributes = Attribute.objects.filter(
            productattribute__product__in=product_ids
        ).annotate(
            product_count=Count('productattribute__product', distinct=True)
        ).filter(
            product_count__gt=1  # Only include attributes used by multiple products
        ).order_by('name')
        
        context['filter_attributes'] = used_attributes
        
        return context

# Admin views for template management
@login_required
@can_add_parts
def admin_template_list(request):
    """List all product templates"""
    templates = ProductTemplate.objects.annotate(
        product_count=Count('product'),
        attribute_count=Count('templateattribute')
    ).order_by('name')
    
    return render(request, 'catalog/admin/template_list.html', {
        'templates': templates
    })

@login_required
@can_add_parts
def admin_template_detail(request, pk):
    """View details of a product template"""
    template = get_object_or_404(ProductTemplate, pk=pk)
    template_attributes = template.templateattribute_set.all().order_by('order')
    
    # Get products using this template
    products = Product.objects.filter(template=template).order_by('name')
    
    return render(request, 'catalog/admin/template_detail.html', {
        'template': template,
        'template_attributes': template_attributes,
        'products': products
    })

@login_required
@can_add_parts
def admin_template_create(request):
    """Create a new product template"""
    if request.method == 'POST':
        # Basic template info
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if not name:
            messages.error(request, 'Template name is required.')
            return redirect('admin-template-create')
        
        # Create the template
        slug = slugify(name)
        
        # Ensure slug is unique
        base_slug = slug
        counter = 1
        while ProductTemplate.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        template = ProductTemplate.objects.create(
            name=name,
            slug=slug,
            description=description
        )
        
        # Process attributes
        attribute_names = request.POST.getlist('attribute_name')
        attribute_types = request.POST.getlist('attribute_type')
        attribute_units = request.POST.getlist('attribute_unit')
        attribute_choices = request.POST.getlist('attribute_choices')
        attribute_required = request.POST.getlist('attribute_required')
        
        for i, attr_name in enumerate(attribute_names):
            if not attr_name:  # Skip empty rows
                continue
                
            attr_type = attribute_types[i] if i < len(attribute_types) else 'text'
            attr_unit = attribute_units[i] if i < len(attribute_units) else ''
            attr_choices = attribute_choices[i] if i < len(attribute_choices) else ''
            attr_required = 'required' in attribute_required and str(i) in attribute_required
            
            # Create or get the attribute
            attr_slug = slugify(attr_name)
            
            # Ensure slug is unique
            base_slug = attr_slug
            counter = 1
            while Attribute.objects.filter(slug=attr_slug).exists():
                attr_slug = f"{base_slug}-{counter}"
                counter += 1
            
            attribute, created = Attribute.objects.get_or_create(
                name=attr_name,
                defaults={
                    'slug': attr_slug,
                    'attr_type': attr_type,
                    'unit': attr_unit,
                    'choices_list': attr_choices
                }
            )
            
            # If attribute exists but different type, update it
            if not created:
                if (attribute.attr_type != attr_type or 
                    attribute.unit != attr_unit or 
                    attribute.choices_list != attr_choices):
                    
                    attribute.attr_type = attr_type
                    attribute.unit = attr_unit
                    attribute.choices_list = attr_choices
                    attribute.save()
            
            # Add to template
            TemplateAttribute.objects.create(
                template=template,
                attribute=attribute,
                order=i,
                required=attr_required
            )
        
        messages.success(request, f'Template "{template.name}" created successfully.')
        return redirect('admin-template-detail', pk=template.id)
    
    # Get all existing attributes for dropdown
    attributes = Attribute.objects.all().order_by('name')
    
    return render(request, 'catalog/admin/template_form.html', {
        'attributes': attributes
    })

@login_required
@can_edit_parts
def admin_template_edit(request, pk):
    """Edit an existing product template"""
    template = get_object_or_404(ProductTemplate, pk=pk)
    
    if request.method == 'POST':
        # Update basic template info
        template.name = request.POST.get('name')
        template.description = request.POST.get('description', '')
        template.save()
        
        # Process attributes - first remove existing ones
        TemplateAttribute.objects.filter(template=template).delete()
        
        # Process attributes
        attribute_names = request.POST.getlist('attribute_name')
        attribute_types = request.POST.getlist('attribute_type')
        attribute_units = request.POST.getlist('attribute_unit')
        attribute_choices = request.POST.getlist('attribute_choices')
        attribute_required = request.POST.getlist('attribute_required')
        
        for i, attr_name in enumerate(attribute_names):
            if not attr_name:  # Skip empty rows
                continue
                
            attr_type = attribute_types[i] if i < len(attribute_types) else 'text'
            attr_unit = attribute_units[i] if i < len(attribute_units) else ''
            attr_choices = attribute_choices[i] if i < len(attribute_choices) else ''
            attr_required = 'required' in attribute_required and str(i) in attribute_required
            
            # Create or get the attribute
            attr_slug = slugify(attr_name)
            
            # Check if this attribute already exists
            try:
                attribute = Attribute.objects.get(
                    Q(name=attr_name) | Q(slug=attr_slug)
                )
                
                # Update the attribute
                attribute.attr_type = attr_type
                attribute.unit = attr_unit
                attribute.choices_list = attr_choices
                attribute.save()
                
            except Attribute.DoesNotExist:
                # Create new attribute
                # Ensure slug is unique
                base_slug = attr_slug
                counter = 1
                while Attribute.objects.filter(slug=attr_slug).exists():
                    attr_slug = f"{base_slug}-{counter}"
                    counter += 1
                
                attribute = Attribute.objects.create(
                    name=attr_name,
                    slug=attr_slug,
                    attr_type=attr_type,
                    unit=attr_unit,
                    choices_list=attr_choices
                )
            
            # Add to template
            TemplateAttribute.objects.create(
                template=template,
                attribute=attribute,
                order=i,
                required=attr_required
            )
        
        messages.success(request, f'Template "{template.name}" updated successfully.')
        return redirect('admin-template-detail', pk=template.id)
    
    # Get current template attributes
    template_attributes = template.templateattribute_set.all().order_by('order')
    
    # Get all existing attributes for dropdown
    attributes = Attribute.objects.all().order_by('name')
    
    return render(request, 'catalog/admin/template_form.html', {
        'template': template,
        'template_attributes': template_attributes,
        'attributes': attributes,
        'is_edit': True
    })

@login_required
@can_delete_parts
def admin_template_delete(request, pk):
    """Delete a product template"""
    template = get_object_or_404(ProductTemplate, pk=pk)
    
    # Check if any products are using this template
    product_count = Product.objects.filter(template=template).count()
    
    if request.method == 'POST':
        # Check for confirmation
        if request.POST.get('confirm_delete') == 'yes':
            # Delete template attributes first
            TemplateAttribute.objects.filter(template=template).delete()
            
            # Delete the template
            template_name = template.name
            template.delete()
            
            messages.success(request, f'Template "{template_name}" deleted successfully.')
            return redirect('admin-template-list')
    
    return render(request, 'catalog/admin/template_confirm_delete.html', {
        'template': template,
        'product_count': product_count
    })