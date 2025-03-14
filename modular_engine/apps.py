from django.apps import AppConfig


class ModularEngineConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modular_engine'
    verbose_name = 'Modular Engine'
    
    def ready(self):
        """Initialize the module registry when the app is ready"""
        # Skip initialization during migrations
        import sys
        if 'makemigrations' in sys.argv or 'migrate' in sys.argv:
            return
            
        # Import signals to register signal handlers
        import modular_engine.signals
            
        # Import here to avoid circular imports
        from modular_engine.module_registry import initialize_module_registry
        initialize_module_registry()
