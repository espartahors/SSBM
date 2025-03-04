# catalog/urls.py
from django.urls import path
from . import views
from .equipment_integration import manage_equipment_parts, ajax_add_part_to_equipment

urlpatterns = [
    # Catalog browsing
    path('', views.catalog_home, name='catalog-home'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('product/<str:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('products/', views.ProductListView.as_view(), name='product-list'),
    
    # Equipment integration
    path('equipment/<int:equipment_id>/parts/', manage_equipment_parts, name='manage-equipment-parts'),
    path('ajax/add-part-to-equipment/', ajax_add_part_to_equipment, name='ajax-add-part-to-equipment'),
    
    # Admin functionality
    path('admin/templates/', views.admin_template_list, name='admin-template-list'),
    path('admin/template/<int:pk>/', views.admin_template_detail, name='admin-template-detail'),
    path('admin/template/new/', views.admin_template_create, name='admin-template-create'),
    path('admin/template/<int:pk>/edit/', views.admin_template_edit, name='admin-template-edit'),
    path('admin/template/<int:pk>/delete/', views.admin_template_delete, name='admin-template-delete'),
]