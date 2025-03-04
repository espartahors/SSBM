# catalog/templatetags/catalog_tags.py
from django import template
from django.utils.safestring import mark_safe
from catalog.models import Category, Product

register = template.Library()

@register.filter
def currency(value):
    """Format a value as currency"""
    if value is None:
        return ''
    return f"${value:.2f}"

@register.filter
def sub(value, arg):
    """Subtract the arg from the value"""
    try:
        return value - arg
    except (ValueError, TypeError):
        return value

@register.simple_tag
def product_attribute(product, attribute_slug, default=''):
    """Get the value of a specific product attribute by slug"""
    try:
        attr = product.attributes.get(attribute__slug=attribute_slug)
        if attr.attribute.attr_type == 'boolean':
            return 'Yes' if attr.value_boolean else 'No'
        return attr.value or default
    except:
        return default

@register.simple_tag
def category_tree(categories=None, current_category=None):
    """Render category tree with proper indentation"""
    if categories is None:
        categories = Category.objects.filter(parent=None)
    
    result = '<ul class="list-unstyled">'
    
    for category in categories:
        active = ''
        if current_category and (current_category.id == category.id or 
                                current_category.is_descendant_of(category)):
            active = 'fw-bold'
        
        result += f'<li class="{active}">'
        result += f'<a href="/catalog/category/{category.slug}/" class="text-decoration-none">{category.name}</a>'
        
        # Add count of products
        product_count = Product.objects.filter(category=category).count()
        if product_count:
            result += f' <span class="badge bg-secondary">{product_count}</span>'
        
        # Render children
        children = category.get_children()
        if children:
            result += '<ul class="list-unstyled ms-3 mt-1 mb-2">'
            for child in children:
                child_active = ''
                if current_category and (current_category.id == child.id or 
                                        current_category.is_descendant_of(child)):
                    child_active = 'fw-bold'
                
                result += f'<li class="{child_active}">'
                result += f'<a href="/catalog/category/{child.slug}/" class="text-decoration-none">{child.name}</a>'
                
                # Add count of products for child
                child_count = Product.objects.filter(category=child).count()
                if child_count:
                    result += f' <span class="badge bg-secondary">{child_count}</span>'
                
                result += '</li>'
            result += '</ul>'
        
        result += '</li>'
    
    result += '</ul>'
    return mark_safe(result)

@register.simple_tag
def breadcrumbs(category=None, product=None):
    """Generate breadcrumbs for category and product pages"""
    crumbs = [{'url': '/catalog/', 'name': 'Catalog'}]
    
    if category:
        # Add ancestors
        for ancestor in category.get_ancestors():
            crumbs.append({
                'url': f'/catalog/category/{ancestor.slug}/',
                'name': ancestor.name
            })
        
        # Add current category
        crumbs.append({
            'url': f'/catalog/category/{category.slug}/',
            'name': category.name
        })
    
    if product:
        # Add category if not already included
        if not category:
            category = product.category
            for ancestor in category.get_ancestors():
                crumbs.append({
                    'url': f'/catalog/category/{ancestor.slug}/',
                    'name': ancestor.name
                })
            
            crumbs.append({
                'url': f'/catalog/category/{category.slug}/',
                'name': category.name
            })
        
        # Add product
        crumbs.append({
            'url': f'/catalog/product/{product.sku}/',
            'name': product.name
        })
    
    # Render breadcrumbs
    result = '<nav aria-label="breadcrumb"><ol class="breadcrumb">'
    
    for i, crumb in enumerate(crumbs):
        if i == len(crumbs) - 1:
            result += f'<li class="breadcrumb-item active" aria-current="page">{crumb["name"]}</li>'
        else:
            result += f'<li class="breadcrumb-item"><a href="{crumb["url"]}">{crumb["name"]}</a></li>'
    
    result += '</ol></nav>'
    return mark_safe(result)