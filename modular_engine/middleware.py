from django.http import Http404
from django.urls import resolve, Resolver404
from django.conf import settings
from modular_engine.module_registry import get_registry


class ModuleURLMiddleware:
    """
    Middleware to control URL access based on module registration and installation status.
    
    This middleware enforces two levels of security:
    1. Only registered modules (in modular engine) can be accessed via URLs
    2. Only installed modules can be accessed (as per previous behavior)
    
    If a URL belongs to a non-registered or non-installed module, a 404 response is returned.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        # Keep a list of allowed core paths that bypass module checks
        self.core_paths = ['', 'admin', 'module', 'auth', 'static', 'media']
        
        # Add additional paths from settings if defined
        if hasattr(settings, 'CORE_PATHS'):
            self.core_paths.extend(settings.CORE_PATHS)
        
    def __call__(self, request):
        # Get the path without the leading slash
        path = request.path.lstrip('/')
        
        # Extract the module ID from the path (first segment)
        if '/' in path:
            module_id = path.split('/')[0]
        else:
            module_id = path
        
        # Skip if this is a core path that should bypass module checks
        if module_id in self.core_paths:
            return self.get_response(request)
        
        # Get the registry
        registry = get_registry()
        
        # First check: Is this a registered module?
        if module_id not in registry.available_modules:
            raise Http404(f"Module '{module_id}' is not registered in the system")
        
        # Second check: Is this module installed/active?
        active_modules = registry.get_active_modules().keys()
        if module_id not in active_modules:
            raise Http404(f"Module '{module_id}' is registered but not installed")
        
        # Continue with the request - module is both registered and installed
        return self.get_response(request)
