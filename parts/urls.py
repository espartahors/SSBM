# parts/urls.py

from django.urls import path
from . import views
from . import views_codification

urlpatterns = [
    # API endpoints
    path('tree-json/', views.part_tree_json, name='part-tree-json'),
    path('tree/', views.parts_tree_view, name='parts-tree'),

    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    
    # Part management
    path('list/', views.PartListView.as_view(), name='part-list'),
    path('new/', views.PartCreateView.as_view(), name='part-create'),
    path('<int:pk>/', views.PartDetailView.as_view(), name='part-detail'),
    path('<int:pk>/edit/', views.PartUpdateView.as_view(), name='part-update'),
    path('<int:pk>/delete/', views.PartDeleteView.as_view(), name='part-delete'),
    
    # Markers
    path('<int:pk>/mark/', views.mark_part, name='mark-part'),
    path('<int:pk>/unmark/', views.unmark_part, name='unmark-part'),
    path('clear-all-marks/', views.clear_all_marks, name='clear-all-marks'),
    path('marked/', views.marked_parts_list, name='marked-parts'),
    
    # Documents
    path('documents/new/', views.DocumentCreateView.as_view(), name='document-create'),
    path('documents/new/<int:part_id>/', views.DocumentCreateView.as_view(), name='document-create-for-part'),
    path('documents/<int:pk>/edit/', views.DocumentUpdateView.as_view(), name='document-update'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document-delete'),
    
    # CSV import/export
    path('import-csv/', views.import_csv_view, name='import-csv'),
    path('export-csv/', views.export_csv_view, name='export-csv'),
    path('import-logs/', views.import_logs_view, name='import-logs'),
    path('import-logs/<int:pk>/', views.import_log_detail, name='import-log-detail'),

    path('codification/', views_codification.codification_viewer, name='codification-viewer'),
]