from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse, clear_url_caches, set_urlconf
from django.views.decorators.http import require_POST
from django.views.generic import ListView
from django.conf import settings

from modular_engine.module_registry import get_registry
from modular_engine.models import Module


class ModuleListView(ListView):
    """View to list all available modules and their status"""
    template_name = 'modular_engine/module_list.html'
    context_object_name = 'modules'

    def get_queryset(self):
        registry = get_registry()
        modules = registry.get_all_modules()

        # Ensure each module has the base_path property
        for module in modules:
            try:
                # Try to get the actual module from the database to get the base_path
                db_module = Module.objects.get(module_id=module['module_id'])
                module['base_path'] = db_module.base_path
            except Module.DoesNotExist:
                module['base_path'] = ''

        return modules


@require_POST
def install_module(request, module_id):
    """View to install a module"""
    registry = get_registry()

    # Get the base path from the POST data if provided
    base_path = request.POST.get('base_path', None)

    success = registry.install_module(module_id, base_path=base_path)

    if success:
        messages.success(
            request, f"Module '{module_id}' installed successfully")
    else:
        messages.error(request, f"Failed to install module '{module_id}'")

    return redirect(reverse('modular_engine:module_list'))


@require_POST
def uninstall_module(request, module_id):
    """View to uninstall a module"""
    registry = get_registry()

    success = registry.uninstall_module(module_id)

    if success:
        messages.success(
            request, f"Module '{module_id}' uninstalled successfully")
    else:
        messages.error(request, f"Failed to uninstall module '{module_id}'")

    return redirect(reverse('modular_engine:module_list'))


@require_POST
def upgrade_module_view(request, module_id):
    """View to upgrade a module"""
    registry = get_registry()

    success = registry.upgrade_module(module_id)

    if success:
        messages.success(
            request, f"Module '{module_id}' upgraded successfully")
    else:
        messages.error(request, f"Failed to upgrade module '{module_id}'")

    return redirect(reverse('modular_engine:module_list'))


@require_POST
def update_module_path(request, module_id):
    """View to update the base path of a module"""
    registry = get_registry()

    # Get the new base path from POST data
    new_base_path = request.POST.get('base_path', '')

    # Use the registry's method to update the path
    success = registry.update_module_path(module_id, new_base_path)

    if success:
        # Get the module to show its name in the success message
        try:
            module = Module.objects.get(module_id=module_id)
            messages.success(
                request, f"Module path for '{module.name}' updated successfully")
        except Module.DoesNotExist:
            messages.success(
                request, f"Module path for '{module_id}' updated successfully")
    else:
        messages.error(
            request, f"Failed to update path for module '{module_id}'")

    return redirect(reverse('modular_engine:module_list'))


def reload_urls(request):
    """View to manually force URL reload"""
    # Clear URL caches
    clear_url_caches()
    
    # Reset the URLconf for the current thread
    set_urlconf(None)
    
    # Reload main URLconf module if needed
    if hasattr(settings, 'ROOT_URLCONF'):
        import sys
        import importlib
        urlconf = settings.ROOT_URLCONF
        if urlconf in sys.modules:
            importlib.reload(sys.modules[urlconf])

    messages.success(request, "URL patterns reloaded successfully")
    return redirect(reverse('modular_engine:module_list'))
