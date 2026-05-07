from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'products'

    def ready(self):
        # Register signal handlers (low stock alerts, etc.)
        from . import signals  # noqa: F401
