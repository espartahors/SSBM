# equipment/urls.py
from django.urls import path
from . import views
from .views import import_equipment_level_csv, equipment_level_tree_view, update_equipment_position

urlpatterns = [
    # Basic CRUD
    path('', views.EquipmentListView.as_view(), name='equipment-list'),
    path('<int:pk>/', views.EquipmentDetailView.as_view(), name='equipment-detail'),
    path('new/', views.EquipmentCreateView.as_view(), name='equipment-create'),
    path('<int:pk>/edit/', views.EquipmentUpdateView.as_view(), name='equipment-update'),
    path('<int:pk>/delete/', views.EquipmentDeleteView.as_view(), name='equipment-delete'),
    
    # Tree views
    path('tree/', equipment_level_tree_view, name='equipment-tree'),
    path('update-position/', update_equipment_position, name='update-equipment-position'),
    
    # CSV import/export
    path('import-csv/', import_equipment_level_csv, name='import-level-csv'),
]