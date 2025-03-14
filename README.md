# Django Modular Engine

Django Modular Engine is a reusable Django application that provides a dynamic module system. It allows you to develop, register, install, and manage modules within your Django project, supporting a plug-and-play architecture.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Core Concepts](#core-concepts)
- [Creating Modules](#creating-modules)
- [Module Management](#module-management)
- [URL Handling](#url-handling)
- [Security Considerations](#security-considerations)
- [Example Module](#example-module)
- [API Reference](#api-reference)
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

3. Add the module middleware to your MIDDLEWARE setting:

```python
MIDDLEWARE = [
    ...
    'modular_engine.middleware.ModuleURLMiddleware',
    ...
]
```

4. Run migrations to create the Module model:

```bash
python manage.py migrate modular_engine
```

5. Start the development server:

```bash
python manage.py runserver
```

6. Visit http://127.0.0.1:8000/module/ to access the module administration page.

## Configuration

Add these settings to your project's settings.py file:

```python
# List of modules that should be available and checked by the middleware
AVAILABLE_MODULES = ['product']

# Core paths that should bypass module checks (optional)
CORE_PATHS = ['login', 'logout']
```

## Core Concepts

The Django Modular Engine is built around these key concepts:

- **Module**: A self-contained application with its own models, views, templates, and URL patterns.
- **Module Registry**: A central registry that keeps track of all available and installed modules.
- **Module Installation**: The process of activating a module in your project.
- **URL Handling**: Dynamic routing to module views based on installation status.

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

## URL Handling

The ModuleURLMiddleware handles routing to module URLs based on the first URL segment:

- URLs starting with a registered and installed module ID will be routed to that module
- URLs for uninstalled modules will return a 404 error
- Core paths (admin, static, etc.) bypass module checks

## Security Considerations

The ModuleURLMiddleware enforces two levels of security:

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
from engine.module_registry import registry

# Register your module
registry.register_module(...)

# Get active modules
active_modules = registry.get_active_modules()

# Install a module
success = registry.install_module('module_id')

# Uninstall a module
success = registry.uninstall_module('module_id')

# Check if upgrade is available
has_upgrade = registry.check_upgrade_available('module_id')

# Upgrade a module
success = registry.upgrade_module('module_id')
```

### Models

#### Module

```python
from engine.models import Module

# Get all installed modules
modules = Module.objects.filter(status='installed')

# Get specific module
module = Module.objects.get(module_id='product')
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.