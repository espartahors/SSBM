# catalog/models.py
from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from equipment.models import Equipment

class Category(MPTTModel):
    """Hierarchical product categories like McMaster-Carr"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    
    class Meta:
        verbose_name_plural = 'Categories'
    
    def __str__(self):
        return self.name

class Attribute(models.Model):
    """Product attributes like material, size, etc."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    unit = models.CharField(max_length=20, blank=True)
    
    # Attribute types for flexible filtering
    TYPE_CHOICES = (
        ('text', 'Text'),
        ('number', 'Number'),
        ('boolean', 'Boolean'),
        ('choice', 'Choice from list'),
    )
    attr_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='text')
    
    # For choice-type attributes
    choices_list = models.TextField(blank=True, help_text="Comma-separated list of choices")
    
    def __str__(self):
        return self.name

class ProductTemplate(models.Model):
    """Template for specific product types (e.g., bearings, motors)"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    attributes = models.ManyToManyField(Attribute, through='TemplateAttribute')
    
    def __str__(self):
        return self.name

class TemplateAttribute(models.Model):
    """Attributes for a specific product template with display order"""
    template = models.ForeignKey(ProductTemplate, on_delete=models.CASCADE)
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    required = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"{self.template.name} - {self.attribute.name}"

class Product(models.Model):
    """Product model representing a part in the catalog"""
    sku = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    # Catalog organization
    category = TreeForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    template = models.ForeignKey(ProductTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Pricing and availability
    price = models.DecimalField(max_digits=10, decimal_places=2)
    on_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Inventory
    stock = models.PositiveIntegerField(default=0)
    
    # References and relations
    related_equipment = models.ManyToManyField(Equipment, blank=True, related_name='catalog_products')
    
    # Technical info
    technical_details = models.TextField(blank=True)
    drawing = models.FileField(upload_to='products/drawings/', blank=True, null=True)
    model_3d = models.FileField(upload_to='products/models/', blank=True, null=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.sku} - {self.name}"

class ProductImage(models.Model):
    """Product images with ordering"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Image for {self.product.sku}"

class ProductAttribute(models.Model):
    """Values for specific attributes of a product"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='attributes')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE)
    value_text = models.TextField(blank=True)
    value_number = models.DecimalField(max_digits=15, decimal_places=6, null=True, blank=True)
    value_boolean = models.BooleanField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.product.sku} - {self.attribute.name}"
        
    @property
    def value(self):
        """Return the appropriate value based on attribute type"""
        if self.attribute.attr_type == 'text' or self.attribute.attr_type == 'choice':
            return self.value_text
        elif self.attribute.attr_type == 'number':
            return self.value_number
        elif self.attribute.attr_type == 'boolean':
            return self.value_boolean
        return None