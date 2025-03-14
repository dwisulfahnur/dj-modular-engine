from django.http import Http404
from django.urls import resolve, Resolver404
from django.conf import settings
from modular_engine.module_registry import get_registry


class ModuleURLMiddleware:
    """
    Middleware to control URL access based on module registration and installation status.

    This middleware enforces two levels of security:
    1. Check if the module is in AVAILABLE_MODULES (if defined in settings)
       - If not in AVAILABLE_MODULES, proceed with registry checks
    2. Check if the module is registered and installed
       - If registered but not installed, return 404

    This ensures that:
    - Modules explicitly listed in AVAILABLE_MODULES are properly checked
    - Modules in the registry are always checked for installation status
    - Paths not matching any module pattern proceed normally
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Keep a list of allowed core paths that bypass module checks
        self.core_paths = ['', 'admin', 'module', 'static', 'media']

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

        # Get the registry regardless - we'll need it for the installation check
        registry = get_registry()

        # If AVAILABLE_MODULES is defined in settings, check if this module is in it
        if hasattr(settings, 'AVAILABLE_MODULES'):
            # If the module is in AVAILABLE_MODULES, enforce full checks
            if module_id in settings.AVAILABLE_MODULES:
                # Check if the module is registered
                if module_id not in registry.available_modules:
                    raise Http404(
                        f"Module '{module_id}' is defined in settings but not registered in the system")

        # Always check if the module is in the registry and installed
        # This ensures modules can't be accessed when uninstalled
        if module_id in registry.available_modules:
            # If it's in the registry, check if it's installed
            active_modules = registry.get_active_modules().keys()
            if module_id not in active_modules:
                raise Http404(
                    f"Module '{module_id}' is registered but not installed")

        # Continue with the request
        return self.get_response(request)
