# Django Modular Engine

Django Modular Engine is a reusable Django application that provides a dynamic module system. It allows you to develop, register, install, and manage modules within your Django project, supporting a plug-and-play architecture.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Core Concepts](#core-concepts)
- [Creating Modules](#creating-modules)
- [Module Management](#module-management)
- [Dynamic Base Paths](#dynamic-base-paths)
- [URL Handling](#url-handling)
- [Security Considerations](#security-considerations)
- [Example Module](#example-module)
- [API Reference](#api-reference)
- [Best Practices](#best-practices)
- [License](#license)

## Installation

```bash
pip install git+https://github.com/dwisulfahnur/dj-modular-engine
```

Or if you're installing from source:

```bash
pip install -e /path/to/dj-modular-engine
```

## Quick Start

1. Add "modular_engine" to your INSTALLED_APPS setting:

```python
INSTALLED_APPS = [
    ...
    'modular_engine',
    ...
]
```

2. Include the engine URLconf in your project urls.py:

```python
path('module/', include('modular_engine.urls', namespace='modular_engine')),
```

3. Add the modular engine middleware to your MIDDLEWARE setting:

```python
MIDDLEWARE = [
    ...
    'modular_engine.middleware.ModularEngineMiddleware',  # Add this for module handling
    ...
]
```

4. Add the dynamic module patterns to your project's urls.py:

```python
from django.contrib import admin
from django.urls import include, path
from modular_engine.module_registry import get_module_url_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('module/', include('modular_engine.urls', namespace='modular_engine')),
    # ... other URL patterns
]

# Add dynamic module URL patterns
urlpatterns += get_module_url_patterns()
```

5. Run migrations to create the Module model:

```bash
python manage.py migrate modular_engine
```

6. Start the development server:

```bash
python manage.py runserver
```

7. Visit http://127.0.0.1:8000/module/ to access the module administration page.

## Configuration

Add these settings to your project's settings.py file:

```python
# List of modules that should be available and checked by the middleware
AVAILABLE_MODULES = ['product']

# Core paths that should bypass module checks (optional)
CORE_PATHS = ['login', 'logout']

# Performance optimization settings - if using earlier versions
# Note: In current version, caching has been removed for direct database access
# URL_RELOAD_MIN_CHECK_INTERVAL = 1  # Minimum seconds between URL reload checks
# URL_RELOAD_MAX_CHECK_INTERVAL = 10  # Maximum seconds between URL reload checks
# URL_RELOAD_ADAPTIVE_FACTOR = 1.5   # How quickly to increase check interval
# MODULE_CACHE_TTL = 30              # Seconds before refreshing module cache
```

## Core Concepts

The Django Modular Engine is built around these key concepts:

- **Module**: A self-contained application with its own models, views, templates, and URL patterns.
- **Module Registry**: A central registry that keeps track of all available and installed modules.
- **Module Installation**: The process of activating a module in your project.
- **Dynamic Base Paths**: Configurable URL base paths for each module.
- **URL Handling**: Dynamic routing to module views based on installation status and base path.

## Creating Modules

To create a module compatible with Django Modular Engine:

1. Create a regular Django app:

```bash
python manage.py startapp product
```

2. Create a `module.py` file in your app with the following structure:

```python
from django.urls import path
from my_module import views

NAME = 'My Module'
VERBOSE_NAME = 'My Custom Module'
DESCRIPTION = 'This module provides custom functionality'
VERSION = '1.0.0'
CATEGORY = 'Core'

# Optional: module URL patterns
urlpatterns = [
    path('list/', views.list_view, name='list'),
    path('detail/<int:pk>/', views.detail_view, name='detail'),
]

# Required: register function
def register(registry):
    """Register this module with the registry"""
    registry.register_module(
        module_id='my_module',
        name=NAME,
        description=DESCRIPTION,
        version=VERSION,
        app_name='my_module',
        url_patterns=urlpatterns,
    )
```

3. Add your module to the `AVAILABLE_MODULES` setting to make it available for installation.

## Module Management

The engine provides an administration interface to manage modules at `/module/`:

- **View Available Modules**: See all modules registered in the system
- **Install/Uninstall Modules**: Activate or deactivate modules
- **Upgrade Modules**: Update module versions when available
- **Configure Base Paths**: Set custom URL base paths for each module
- **Reload URL Configuration**: Manually reload URL patterns if needed

## Dynamic Base Paths

A key feature of the modular engine is the ability to configure custom base paths for each module:

### Installing a Module with a Custom Base Path

When installing a module, you can specify a custom base path:

1. Through the UI: Use the provided input field when installing a module
2. Through the API: Provide the `base_path` parameter when calling `install_module`

### Special Base Path Values

- **Empty**: If left empty, the module's ID will be used as the base path
- **"/"**: Use a forward slash to mount the module at the root URL
- **Custom value**: Any other value will be used as-is

### Updating a Module's Base Path

You can update a module's base path at any time:

1. Through the UI: Click the "Update Path" button for an installed module
2. Through the API: Call `registry.update_module_path(module_id, new_base_path)`

The URL patterns will be automatically reloaded, making the module immediately accessible at its new path.

## URL Handling

The modular engine handles URL routing dynamically:

- The `ModularEngineMiddleware` now only handles routes that start with 'modular_engine/'
- URL patterns are automatically routed to the appropriate modules based on the path segments
- URL caches are automatically cleared when modules are installed, uninstalled, or paths are updated
- You can manually reload URL patterns using the "Reload URL Configuration" button on the module management page

### How URL Routing Works

1. The middleware only processes paths that start with 'modular_engine/'
2. For these paths, the second segment is extracted to identify the module
3. If the module is registered and installed, the request is routed to that module's URL patterns
4. If the module is not installed or doesn't exist, an Http404 error is raised
5. Core paths (admin, static, module, etc.) always bypass module checks even within the modular_engine namespace

### Performance Considerations

The URL handling system has been optimized for efficiency:

- **Direct Database Access**: Module information is now queried directly from the database for each request
- **Focused Processing**: The middleware only processes paths that need module-based routing
- **Minimal Overhead**: The middleware focuses solely on module URL access control
- **Core Path Exclusions**: Predefined core paths bypass module checks to reduce processing time

## Security Considerations

The ModularEngineMiddleware enforces two levels of security:

1. Only modules listed in `AVAILABLE_MODULES` (if defined) are checked
2. For registered modules, only installed modules can be accessed

This ensures that:

- Modules explicitly listed in `AVAILABLE_MODULES` are properly checked
- Modules in the registry are always checked for installation status
- Paths not matching any module pattern proceed normally

## Example Module

Here's a complete example of a product module:

```python
# product/module.py
from django.urls import path
from product import views

NAME = 'Products'
VERBOSE_NAME = 'Product Management'
DESCRIPTION = 'Manage products in your system'
VERSION = '1.0.0'
CATEGORY = 'Business'

# Define URL patterns for the module
urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('create/', views.product_create, name='product_create'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    path('<int:pk>/update/', views.product_update, name='product_update'),
    path('<int:pk>/delete/', views.product_delete, name='product_delete'),
]

def register(registry):
    """Register this module with the registry"""
    registry.register_module(
        module_id='product',
        name=NAME,
        description=DESCRIPTION,
        version=VERSION,
        app_name='product',
        url_patterns=urlpatterns,
    )
```

## API Reference

### Module Registry

```python
from modular_engine.module_registry import registry

# Register your module
registry.register_module(...)

# Get active modules
active_modules = registry.get_active_modules()

# Install a module (optionally with a custom base path)
success = registry.install_module('module_id', base_path='custom_path')

# Uninstall a module
success = registry.uninstall_module('module_id')

# Check if upgrade is available
has_upgrade = registry.check_upgrade_available('module_id')

# Upgrade a module
success = registry.upgrade_module('module_id')

# Update a module's base path
success = registry.update_module_path('module_id', 'new_base_path')
```

### Models

#### Module

```python
from modular_engine.models import Module

# Get all installed modules
modules = Module.objects.filter(status='installed')

# Get specific module
module = Module.objects.get(module_id='product')

# Get module's URL path
base_path = module.get_url_path()  # Returns base_path if set, otherwise module_id
```

### Signal Handlers

The engine includes signal handlers for key events:

```python
from modular_engine.signals import module_path_changed

# Listen for module path changes
@receiver(module_path_changed)
def on_module_path_changed(sender, module_id, old_path, new_path, **kwargs):
    # Do something when a module's path changes
    pass
```

## Best Practices

1. **Module Isolation**: Keep modules self-contained with minimal dependencies on other modules.
2. **Base Path Selection**: Choose meaningful base paths that describe the module's purpose.
3. **Root Path Usage**: Be careful when installing modules at the root path ("/") to avoid conflicts.
4. **URL Reload**: Use the "Reload URL Configuration" button if you notice URL routing issues.
5. **Testing**: Test your modules with different base path configurations to ensure they work correctly.
6. **Route Structure**: All module routes should be accessible under the 'modular_engine/' prefix.

## License

This project is licensed under the MIT License - see the LICENSE file for details.