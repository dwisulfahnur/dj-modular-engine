from django.http import Http404
from django.conf import settings
from modular_engine.models import Module
import time


class ModularEngineMiddleware:
    """
    Combined middleware for Django Modular Engine that handles:
    1. Module URL access control based on installation status

    Notes:
    - URLs will only be reloaded manually via the module list page button
    - Or when modules are installed/uninstalled/updated

    This middleware focuses on performance by:
    - Caching module information to reduce database queries
    - Only handling necessary module access control
    """

    def __init__(self, get_response):
        self.get_response = get_response

        # Module access control settings
        self.core_paths = ['admin', 'module', 'static', 'media']

        # Add additional core paths from settings if defined
        if hasattr(settings, 'CORE_PATHS'):
            self.core_paths.extend(settings.CORE_PATHS)

    def __call__(self, request):
        # Get the path without the leading slash
        path = request.path.lstrip('/')

        # Check if the path starts with 'modular_engine'
        if not path.startswith('modular_engine'):
            # If not, bypass this middleware
            return self.get_response(request)

        # === STEP 2: Apply module URL access control ===
        # For paths that start with 'modular_engine', extract the second segment
        path_segments = path.split('/')
        
        # We need at least two segments (modular_engine/module_name)
        if len(path_segments) < 2:
            return self.get_response(request)
            
        # The second segment is the module name
        module_segment = path_segments[1]
        
        # Skip if this is a core path that should bypass module checks
        if module_segment in self.core_paths:
            return self.get_response(request)

        # Get installed modules directly from the database
        installed_modules = self.get_installed_modules()

        # Determine which module this request is for based on the path
        target_module_id = None

        # Check if this module segment maps to an installed module
        if module_segment in installed_modules:
            target_module_id = installed_modules[module_segment]

        # If we've identified a module, check if it's accessible
        if target_module_id:
            # If AVAILABLE_MODULES is defined in settings, check if this module is allowed
            if hasattr(settings, 'AVAILABLE_MODULES'):
                if target_module_id not in settings.AVAILABLE_MODULES:
                    raise Http404(
                        f"Module '{target_module_id}' is not available")

            # Check if the module is installed
            try:
                module = Module.objects.get(module_id=target_module_id)
                if module.status != 'installed':
                    raise Http404(
                        f"Module '{target_module_id}' is not installed")
            except Module.DoesNotExist:
                raise Http404(f"Module '{target_module_id}' does not exist")

        # Continue with the request
        return self.get_response(request)

    def get_installed_modules(self):
        """
        Get a mapping of base paths to module IDs for all installed modules.
        """
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
            # If there's an error (e.g., table doesn't exist), return empty dict
            pass

        return installed_modules
