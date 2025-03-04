# catalog/admin.py
from django.contrib import admin
from django.utils.html import format_html
from mptt.admin import MPTTModelAdmin
from django.db.models import Count
from .models import (
    Category, 
    Attribute, 
    ProductTemplate, 
    TemplateAttribute,
    Product, 
    ProductAttribute, 
    ProductImage
)

class CategoryAdmin(MPTTModelAdmin):
    """Admin interface for categories with tree view"""
    list_display = ('name', 'slug', 'parent', 'product_count')
    list_filter = ('parent',)
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(product_count=Count('product'))
        return queryset
    
    def product_count(self, obj):
        return obj.product_count
    product_count.short_description = 'Products'
    product_count.admin_order_field = 'product_count'

class AttributeAdmin(admin.ModelAdmin):
    """Admin interface for attributes"""
    list_display = ('name', 'slug', 'attr_type', 'unit', 'choices_preview')
    list_filter = ('attr_type',)
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    def choices_preview(self, obj):
        if obj.attr_type == 'choice' and obj.choices_list:
            choices = obj.choices_list.split(',')
            if len(choices) > 3:
                return f"{', '.join(choices[:3])}..."
            return obj.choices_list
        return '-'
    choices_preview.short_description = 'Choices'

class TemplateAttributeInline(admin.TabularInline):
    """Inline editor for template attributes"""
    model = TemplateAttribute
    extra = 1
    raw_id_fields = ('attribute',)

class ProductTemplateAdmin(admin.ModelAdmin):
    """Admin interface for product templates"""
    list_display = ('name', 'slug', 'attribute_count', 'description_preview')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [TemplateAttributeInline]
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(attribute_count=Count('templateattribute'))
        return queryset
    
    def attribute_count(self, obj):
        return obj.attribute_count
    attribute_count.short_description = 'Attributes'
    attribute_count.admin_order_field = 'attribute_count'
    
    def description_preview(self, obj):
        if obj.description:
            return obj.description[:50] + ('...' if len(obj.description) > 50 else '')
        return '-'
    description_preview.short_description = 'Description'

class ProductAttributeInline(admin.TabularInline):
    """Inline editor for product attributes"""
    model = ProductAttribute
    extra = 1
    raw_id_fields = ('attribute',)

class ProductImageInline(admin.TabularInline):
    """Inline editor for product images"""
    model = ProductImage
    extra = 1

class ProductAdmin(admin.ModelAdmin):
    """Admin interface for products"""
    list_display = ('sku', 'name', 'category', 'template', 'price_display', 'stock_status', 'image_preview')
    list_filter = ('category', 'template', 'stock', 'on_sale')
    search_fields = ('sku', 'name', 'description')
    list_per_page = 25
    filter_horizontal = ('related_equipment',)
    inlines = [ProductAttributeInline, ProductImageInline]
    fieldsets = (
        (None, {
            'fields': ('sku', 'name', 'description')
        }),
        ('Categorization', {
            'fields': ('category', 'template')
        }),
        ('Pricing', {
            'fields': ('price', 'on_sale', 'sale_price')
        }),
        ('Inventory', {
            'fields': ('stock',)
        }),
        ('Relations', {
            'fields': ('related_equipment',)
        }),
        ('Technical', {
            'fields': ('technical_details', 'drawing', 'model_3d')
        }),
    )
    
    def price_display(self, obj):
        if obj.on_sale and obj.sale_price:
            return format_html(
                '<span style="text-decoration: line-through">${:.2f}</span> <span style="color: red">${:.2f}</span>',
                obj.price, obj.sale_price
            )
        return f'${obj.price:.2f}'
    price_display.short_description = 'Price'
    
    def stock_status(self, obj):
        if obj.stock <= 0:
            return format_html('<span style="color: red">Out of stock</span>')
        elif obj.stock < 10:
            return format_html('<span style="color: orange">Low stock ({0})</span>', obj.stock)
        return format_html('<span style="color: green">In stock ({0})</span>', obj.stock)
    stock_status.short_description = 'Stock'
    
    def image_preview(self, obj):
        try:
            first_image = obj.images.first()
            if first_image and first_image.image:
                return format_html('<img src="{0}" width="50" height="50" style="object-fit: contain;" />', first_image.image.url)
        except Exception:
            pass
        return '-'
    image_preview.short_description = 'Image'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('images', 'category')

admin.site.register(Category, CategoryAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(ProductTemplate, ProductTemplateAdmin)
admin.site.register(Product, ProductAdmin)