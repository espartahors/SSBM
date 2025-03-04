# catalog/signals.py
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.dispatch import receiver
from django.utils.text import slugify

from .models import Category, Product, ProductTemplate

@receiver(pre_save, sender=Category)
def category_pre_save(sender, instance, **kwargs):
    """Generate slug for new categories"""
    if not instance.slug:
        instance.slug = slugify(instance.name)
        
        # Ensure slug is unique
        original_slug = instance.slug
        counter = 1
        
        while Category.objects.filter(slug=instance.slug).exists():
            instance.slug = f"{original_slug}-{counter}"
            counter += 1

@receiver(pre_save, sender=ProductTemplate)
def template_pre_save(sender, instance, **kwargs):
    """Generate slug for new templates"""
    if not instance.slug:
        instance.slug = slugify(instance.name)
        
        # Ensure slug is unique
        original_slug = instance.slug
        counter = 1
        
        while ProductTemplate.objects.filter(slug=instance.slug).exists():
            instance.slug = f"{original_slug}-{counter}"
            counter += 1

@receiver(post_save, sender=Product)
def product_post_save(sender, instance, created, **kwargs):
    """When a product is created with a template, create empty attribute values"""
    if created and instance.template:
        # Get all attributes from the template
        template_attrs = instance.template.templateattribute_set.all()
        
        # Create empty attribute values for each template attribute
        for template_attr in template_attrs:
            attr = template_attr.attribute
            
            # Skip if attribute already exists
            if instance.attributes.filter(attribute=attr).exists():
                continue
                
            # Create appropriate attribute value based on type
            kwargs = {'product': instance, 'attribute': attr}
            
            # Initialize with empty/null values
            if attr.attr_type == 'text' or attr.attr_type == 'choice':
                kwargs['value_text'] = ''
            elif attr.attr_type == 'number':
                pass  # Use default null value
            elif attr.attr_type == 'boolean':
                pass  # Use default null value
                
            instance.attributes.create(**kwargs)