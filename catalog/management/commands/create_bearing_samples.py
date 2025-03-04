# catalog/management/commands/create_bearing_samples.py
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from catalog.models import (
    Category, Attribute, ProductTemplate, TemplateAttribute,
    Product, ProductAttribute, ProductImage
)
import random
import os
from decimal import Decimal

class Command(BaseCommand):
    help = 'Creates sample bearing products and categories'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Creating bearing sample data...'))
        
        # Transaction to ensure all-or-nothing creation
        try:
            with transaction.atomic():
                self.create_categories()
                attributes = self.create_attributes()
                bearing_template = self.create_template(attributes)
                self.create_sample_bearings(bearing_template, attributes)
                
            self.stdout.write(self.style.SUCCESS('Successfully created bearing sample data'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error creating sample data: {e}'))
    
    def create_categories(self):
        """Create category hierarchy for bearings"""
        self.stdout.write('Creating categories...')
        
        # Main categories
        components, _ = Category.objects.get_or_create(
            slug='mechanical-components',
            defaults={
                'name': 'Mechanical Components',
                'description': 'Mechanical parts and components for various applications',
            }
        )
        
        # Bearing category and subcategories
        bearings, _ = Category.objects.get_or_create(
            slug='bearings',
            defaults={
                'name': 'Bearings',
                'description': 'Bearings for rotational and linear motion',
                'parent': components
            }
        )
        
        # Create bearing subcategories
        bearing_types = [
            {
                'name': 'Ball Bearings',
                'slug': 'ball-bearings',
                'description': 'Bearings that use balls as rolling elements'
            },
            {
                'name': 'Roller Bearings',
                'slug': 'roller-bearings',
                'description': 'Bearings that use rollers as rolling elements'
            },
            {
                'name': 'Linear Bearings',
                'slug': 'linear-bearings',
                'description': 'Bearings designed for linear motion along a shaft'
            },
            {
                'name': 'Thrust Bearings',
                'slug': 'thrust-bearings',
                'description': 'Bearings designed to support axial loads'
            },
            {
                'name': 'Needle Bearings',
                'slug': 'needle-bearings',
                'description': 'Bearings that use long, thin rollers'
            }
        ]
        
        for bearing_type in bearing_types:
            Category.objects.get_or_create(
                slug=bearing_type['slug'],
                defaults={
                    'name': bearing_type['name'],
                    'description': bearing_type['description'],
                    'parent': bearings
                }
            )
        
        return bearings
    
    def create_attributes(self):
        """Create attributes for bearings"""
        self.stdout.write('Creating bearing attributes...')
        
        bearing_attrs = [
            {
                'name': 'Inner Diameter', 
                'slug': 'inner-diameter', 
                'attr_type': 'number', 
                'unit': 'mm',
                'description': 'Internal diameter of the bearing'
            },
            {
                'name': 'Outer Diameter', 
                'slug': 'outer-diameter', 
                'attr_type': 'number', 
                'unit': 'mm',
                'description': 'External diameter of the bearing'
            },
            {
                'name': 'Thickness', 
                'slug': 'thickness', 
                'attr_type': 'number', 
                'unit': 'mm',
                'description': 'Width/thickness of the bearing'
            },
            {
                'name': 'Material', 
                'slug': 'material', 
                'attr_type': 'choice',
                'choices_list': 'Steel,Stainless Steel,Chrome Steel,Ceramic,Plastic',
                'description': 'Bearing material'
            },
            {
                'name': 'Bearing Type', 
                'slug': 'bearing-type', 
                'attr_type': 'choice',
                'choices_list': 'Ball,Roller,Needle,Thrust,Linear',
                'description': 'Type of bearing design'
            },
            {
                'name': 'Load Rating', 
                'slug': 'load-rating', 
                'attr_type': 'number',
                'unit': 'N',
                'description': 'Maximum load capacity'
            },
            {
                'name': 'Max RPM', 
                'slug': 'max-rpm', 
                'attr_type': 'number',
                'unit': 'RPM',
                'description': 'Maximum rotation speed'
            },
            {
                'name': 'Sealed', 
                'slug': 'sealed', 
                'attr_type': 'boolean',
                'description': 'Whether bearing has seals'
            }
        ]
        
        # Create the attributes
        attribute_objects = {}
        for attr in bearing_attrs:
            obj, created = Attribute.objects.get_or_create(
                slug=attr['slug'],
                defaults={
                    'name': attr['name'],
                    'attr_type': attr['attr_type'],
                    'unit': attr.get('unit', ''),
                    'description': attr.get('description', ''),
                    'choices_list': attr.get('choices_list', '')
                }
            )
            attribute_objects[attr['slug']] = obj
            
            if created:
                self.stdout.write(f'  Created attribute: {attr["name"]}')
        
        return attribute_objects
    
    def create_template(self, attributes):
        """Create bearing template with attributes"""
        self.stdout.write('Creating bearing template...')
        
        # Create bearing template
        bearing_template, created = ProductTemplate.objects.get_or_create(
            slug='bearing',
            defaults={
                'name': 'Bearing',
                'description': 'Template for all types of bearings'
            }
        )
        
        if created:
            self.stdout.write('  Created bearing template')
        
        # Add attributes to template with ordering
        required_attrs = ['inner-diameter', 'outer-diameter', 'thickness', 'bearing-type']
        
        for i, (slug, attr) in enumerate(attributes.items()):
            TemplateAttribute.objects.get_or_create(
                template=bearing_template,
                attribute=attr,
                defaults={
                    'order': i,
                    'required': slug in required_attrs
                }
            )
        
        return bearing_template
    
    def create_sample_bearings(self, template, attributes):
        """Create sample bearing products"""
        self.stdout.write('Creating sample bearing products...')
        
        # Standard bearing specifications (based on common 608, 6201, 6205 bearings, etc.)
        bearing_specs = [
            # Ball bearings
            {
                'sku': 'B-608-ZZ',
                'name': 'Ball Bearing 608-ZZ',
                'category_slug': 'ball-bearings',
                'inner_diameter': 8,
                'outer_diameter': 22,
                'thickness': 7,
                'bearing_type': 'Ball',
                'material': 'Chrome Steel',
                'load_rating': 1800,
                'max_rpm': 32000,
                'sealed': True,
                'price': Decimal('5.99')
            },
            {
                'sku': 'B-6201-2RS',
                'name': 'Ball Bearing 6201-2RS',
                'category_slug': 'ball-bearings',
                'inner_diameter': 12,
                'outer_diameter': 32,
                'thickness': 10,
                'bearing_type': 'Ball',
                'material': 'Chrome Steel',
                'load_rating': 3100,
                'max_rpm': 26000,
                'sealed': True,
                'price': Decimal('7.49')
            },
            {
                'sku': 'B-6205-C3',
                'name': 'Ball Bearing 6205-C3',
                'category_slug': 'ball-bearings',
                'inner_diameter': 25,
                'outer_diameter': 52,
                'thickness': 15,
                'bearing_type': 'Ball',
                'material': 'Steel',
                'load_rating': 7800,
                'max_rpm': 17000,
                'sealed': False,
                'price': Decimal('14.95')
            },
            
            # Roller bearings
            {
                'sku': 'R-NA4900',
                'name': 'Needle Roller Bearing NA4900',
                'category_slug': 'needle-bearings',
                'inner_diameter': 10,
                'outer_diameter': 22,
                'thickness': 13,
                'bearing_type': 'Needle',
                'material': 'Steel',
                'load_rating': 4900,
                'max_rpm': 12000,
                'sealed': False,
                'price': Decimal('21.99')
            },
            {
                'sku': 'R-NU2205E',
                'name': 'Cylindrical Roller Bearing NU2205E',
                'category_slug': 'roller-bearings',
                'inner_diameter': 25,
                'outer_diameter': 52,
                'thickness': 18,
                'bearing_type': 'Roller',
                'material': 'Steel',
                'load_rating': 12500,
                'max_rpm': 10000,
                'sealed': False,
                'price': Decimal('31.75')
            },
            
            # Thrust bearings
            {
                'sku': 'T-51105',
                'name': 'Thrust Ball Bearing 51105',
                'category_slug': 'thrust-bearings',
                'inner_diameter': 25,
                'outer_diameter': 42,
                'thickness': 11,
                'bearing_type': 'Thrust',
                'material': 'Steel',
                'load_rating': 9000,
                'max_rpm': 5000,
                'sealed': False,
                'price': Decimal('18.25')
            },
            
            # Linear bearings
            {
                'sku': 'L-LM8UU',
                'name': 'Linear Bearing LM8UU',
                'category_slug': 'linear-bearings',
                'inner_diameter': 8,
                'outer_diameter': 15,
                'thickness': 24,
                'bearing_type': 'Linear',
                'material': 'Steel',
                'load_rating': 350,
                'max_rpm': 0,  # Not applicable for linear bearings
                'sealed': True,
                'price': Decimal('4.99')
            }
        ]
        
        # Create each bearing
        for spec in bearing_specs:
            category = Category.objects.get(slug=spec['category_slug'])
            
            # Create the product
            product, created = Product.objects.get_or_create(
                sku=spec['sku'],
                defaults={
                    'name': spec['name'],
                    'description': f"Standard {spec['bearing_type']} bearing with {spec['inner_diameter']}mm inner diameter, {spec['outer_diameter']}mm outer diameter, and {spec['thickness']}mm thickness. Made of {spec['material']}.",
                    'category': category,
                    'template': template,
                    'price': spec['price'],
                    'stock': random.randint(10, 100),
                    'technical_details': f"This bearing is suitable for applications requiring up to {spec['load_rating']}N load and {spec['max_rpm']}RPM. {'Sealed design protects against dust and debris.' if spec['sealed'] else 'Open design for high-speed applications.'}"
                }
            )
            
            if created:
                self.stdout.write(f'  Created product: {spec["name"]}')
                
                # Create product attributes
                self.create_product_attributes(product, attributes, spec)
                
                # In a real implementation, you would create actual product images here
                # For demonstration, we'll just create a placeholder
                self.create_placeholder_image(product)
    
    def create_product_attributes(self, product, attributes, spec):
        """Create attributes for a specific product"""
        # Map spec values to attribute models
        attr_values = {
            'inner_diameter': {'attr': attributes['inner-diameter'], 'value': spec['inner_diameter'], 'field': 'value_number'},
            'outer_diameter': {'attr': attributes['outer-diameter'], 'value': spec['outer_diameter'], 'field': 'value_number'},
            'thickness': {'attr': attributes['thickness'], 'value': spec['thickness'], 'field': 'value_number'},
            'material': {'attr': attributes['material'], 'value': spec['material'], 'field': 'value_text'},
            'bearing_type': {'attr': attributes['bearing-type'], 'value': spec['bearing_type'], 'field': 'value_text'},
            'load_rating': {'attr': attributes['load-rating'], 'value': spec['load_rating'], 'field': 'value_number'},
            'max_rpm': {'attr': attributes['max-rpm'], 'value': spec['max_rpm'], 'field': 'value_number'},
            'sealed': {'attr': attributes['sealed'], 'value': spec['sealed'], 'field': 'value_boolean'},
        }
        
        # Create attribute values for the product
        for key, data in attr_values.items():
            kwargs = {
                'product': product,
                'attribute': data['attr'],
                data['field']: data['value']
            }
            ProductAttribute.objects.get_or_create(**kwargs)
    
    def create_placeholder_image(self, product):
        """Create a placeholder image for a product"""
        # In a real application, you would use actual images
        # For demonstration purposes, we'll just create a record
        ProductImage.objects.create(
            product=product,
            alt_text=f"Image of {product.name}",
            order=0
        )