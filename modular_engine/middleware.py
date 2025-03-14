from django.http import Http404
from django.conf import settings
from modular_engine.models import Module
from modular_engine.signals import get_last_url_change, force_reload_urls
import time


class URLReloadMiddleware:
    """
    Middleware that checks if URL patterns need to be reloaded.
    
    This middleware monitors for URL configuration changes and reloads them when needed.
    It works by comparing timestamps of when URLs were last changed.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.last_check = 0
        self.check_interval = getattr(settings, 'URL_RELOAD_CHECK_INTERVAL', 2)  # in seconds
        
    def __call__(self, request):
        # Only check periodically to avoid performance impact
        current_time = time.time()
        if current_time - self.last_check > self.check_interval:
            self.last_check = current_time
            
            # Get last URL change timestamp
            last_change = get_last_url_change()
            
            # If URLs have been changed since we last loaded them
            if last_change > self.last_check - self.check_interval:
                # Force reload
                force_reload_urls()
        
        # Continue with request processing
        return self.get_response(request)


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
        self.core_paths = ['admin', 'module', 'static', 'media']

        # Add additional paths from settings if defined
        if hasattr(settings, 'CORE_PATHS'):
            self.core_paths.extend(settings.CORE_PATHS)

    def __call__(self, request):
        # Get the path without the leading slash
        path = request.path.lstrip('/')

        # Extract the first segment of the path
        if '/' in path:
            first_segment = path.split('/')[0]
        else:
            first_segment = path

        # Skip if this is a core path that should bypass module checks
        if first_segment in self.core_paths:
            return self.get_response(request)

        # Get all installed modules and their paths
        installed_modules = {}

        try:
            # Query all installed modules
            modules = Module.objects.filter(status='installed')
            
            # Create a mapping of paths to module_ids
            for module in modules:
                if module.base_path == '/':
                    # For root path, use empty string as the key
                    installed_modules[''] = module.module_id
                else:
                    # Use the custom base path or module_id as the key
                    path_key = module.base_path if module.base_path else module.module_id
                    installed_modules[path_key] = module.module_id
        except:
            # If there's an error (e.g., table doesn't exist), continue
            pass

        # Determine which module this request is for based on the path
        target_module_id = None

        # Check if the path is for the root module
        if first_segment == '' and '' in installed_modules:
            target_module_id = installed_modules['']
        elif first_segment in installed_modules:
            target_module_id = installed_modules[first_segment]

        # If we've identified a module, check if it's accessible
        if target_module_id:
            # If AVAILABLE_MODULES is defined in settings, check if this module is allowed
            if hasattr(settings, 'AVAILABLE_MODULES'):
                if target_module_id not in settings.AVAILABLE_MODULES:
                    # Module is not in AVAILABLE_MODULES, so access is denied
                    raise Http404(f"Module '{target_module_id}' is not available")

            # Check if the module is installed
            try:
                module = Module.objects.get(module_id=target_module_id)
                if module.status != 'installed':
                    raise Http404(f"Module '{target_module_id}' is not installed")
            except Module.DoesNotExist:
                raise Http404(f"Module '{target_module_id}' does not exist")

        # Continue with the request
        return self.get_response(request)
