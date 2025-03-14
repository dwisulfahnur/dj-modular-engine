import importlib
import logging
from django.apps import apps
from django.conf import settings
from django.urls import clear_url_caches, include, path
from django.utils import timezone
from django.db import connection
from django.db import DatabaseError

logger = logging.getLogger(__name__)


class ModuleRegistry:
    """Class to handle registration and management of modules"""

    def __init__(self):
        self.modules = {}
        self.available_modules = {}

    def register_module(self, module_id, name, description, version, app_name, setup_func=None, url_patterns=None):
        """Register a module in the registry"""
        self.available_modules[module_id] = {
            'module_id': module_id,
            'name': name,
            'description': description,
            'version': version,
            'app_name': app_name,
            'setup_func': setup_func,
            'url_patterns': url_patterns,
        }

    def install_module(self, module_id):
        """Install a module and mark it as installed in the database"""
        from modular_engine.models import Module

        if module_id not in self.available_modules:
            logger.error(f"Module {module_id} not found in registry")
            return False

        module_info = self.available_modules[module_id]

        # Run setup function if provided
        if module_info.get('setup_func'):
            try:
                module_info['setup_func']()
            except Exception as e:
                logger.error(
                    f"Error running setup for module {module_id}: {e}")
                return False

        # Check if module already exists to determine dates
        module_exists = Module.objects.filter(module_id=module_id).exists()

        defaults = {
            'name': module_info['name'],
            'description': module_info['description'],
            'version': module_info['version'],
            'status': 'installed',
        }

        # Set dates based on whether the module exists
        if not module_exists:
            defaults['install_date'] = timezone.now()
        else:
            defaults['update_date'] = timezone.now()

        # Update or create the module record
        module, created = Module.objects.update_or_create(
            module_id=module_id,
            defaults=defaults
        )

        # Add module to active modules
        self.modules[module_id] = module_info

        # Reload URLs
        self._reload_urls()

        return True

    def uninstall_module(self, module_id):
        """Uninstall a module and mark it as not installed in the database"""
        from modular_engine.models import Module

        if module_id not in self.modules:
            logger.error(f"Module {module_id} not found in active modules")
            return False

        # Update the module record
        try:
            module = Module.objects.get(module_id=module_id)
            module.status = 'not_installed'
            module.save()
        except Module.DoesNotExist:
            logger.error(f"Module {module_id} not found in database")
            return False

        # Remove module from active modules
        self.modules.pop(module_id, None)

        # Reload URLs
        self._reload_urls()

        return True

    def check_upgrade_available(self, module_id):
        """Check if an upgrade is available for a module"""
        from modular_engine.models import Module

        if module_id not in self.available_modules:
            return False

        try:
            module = Module.objects.get(module_id=module_id)
            registered_version = self.available_modules[module_id]['version']

            if module.version != registered_version:
                return True

            return False
        except Module.DoesNotExist:
            return False

    def upgrade_module(self, module_id):
        """Upgrade a module to the latest version"""
        from modular_engine.models import Module

        if module_id not in self.available_modules:
            logger.error(f"Module {module_id} not found in registry")
            return False

        if module_id not in self.modules:
            logger.error(f"Module {module_id} not installed")
            return False

        module_info = self.available_modules[module_id]

        try:
            module = Module.objects.get(module_id=module_id)

            # Update the module record
            module.version = module_info['version']
            module.update_date = timezone.now()
            module.status = 'installed'
            module.save()

            # Update active modules
            self.modules[module_id] = module_info

            return True
        except Module.DoesNotExist:
            logger.error(f"Module {module_id} not found in database")
            return False

    def get_active_modules(self):
        """Get list of active modules"""
        return self.modules

    def get_all_modules(self):
        """Get list of all registered modules with their status"""
        from modular_engine.models import Module

        result = []

        for module_id, module_info in self.available_modules.items():
            status = 'not_installed'
            version = module_info['version']
            install_date = None
            update_date = None

            try:
                module = Module.objects.get(module_id=module_id)
                status = module.status
                install_date = module.install_date
                update_date = module.update_date

                # Check if upgrade is available
                if status == 'installed' and self.check_upgrade_available(module_id):
                    status = 'upgrade_available'
                    module.status = status
                    module.save()
            except Module.DoesNotExist:
                pass

            result.append({
                'module_id': module_id,
                'name': module_info['name'],
                'description': module_info['description'],
                'version': version,
                'status': status,
                'install_date': install_date,
                'update_date': update_date
            })

        return result

    def _reload_urls(self):
        """Reload URLs to include active modules"""
        # This is a placeholder - actual URL reloading is implemented
        # in the urlconf section using dynamic imports
        clear_url_caches()


# Singleton instance of the registry
registry = ModuleRegistry()


def initialize_module_registry():
    # Avoid database access during app initialization
    if not connection.is_usable():
        return
        
    # Check if the table exists before trying to query it
    try:
        # Load modules from the database
        from modular_engine.models import Module
        installed_modules = Module.objects.filter(status='installed')

        # Register available modules from settings
        if hasattr(settings, 'AVAILABLE_MODULES'):
            for module_config in settings.AVAILABLE_MODULES:
                try:
                    module_app = module_config['app_name']

                    # Try to import the module
                    module = importlib.import_module(f"{module_app}.module")

                    # Register the module
                    if hasattr(module, 'register'):
                        module.register(registry)
                except (ImportError, AttributeError) as e:
                    logger.error(f"Error loading module {module_config}: {e}")

        # Activate installed modules
        for module in installed_modules:
            if module.module_id in registry.available_modules:
                registry.modules[module.module_id] = registry.available_modules[module.module_id]

                # Check for available upgrades
                if registry.check_upgrade_available(module.module_id):
                    module.status = 'upgrade_available'
                    module.save()
            else:
                # Module was installed but is no longer available
                module.status = 'not_installed'
                module.save()
    except DatabaseError:
        # Table doesn't exist yet, migrations haven't been run
        pass

    return registry


# Helper function to get the registry
def get_registry():
    return registry


# Dynamic module URL patterns
def get_module_url_patterns():
    registry = get_registry()
    module_patterns = []
    
    # Include URL patterns for all available modules
    # Our middleware will prevent access to uninstalled modules
    for module_id, module_info in registry.available_modules.items():
        if module_info.get('url_patterns'):
            module_patterns.append(
                path(f"{module_id}/", include(module_info['url_patterns']))
            )
    
    return module_patterns
