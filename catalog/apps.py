# catalog/apps.py
from django.apps import AppConfig


class CatalogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'catalog'
    verbose_name = 'Parts Catalog'
    
    def ready(self):
        # Import signals handlers
        import catalog.signals