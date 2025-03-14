from django.contrib import messages
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import ListView

from modular_engine.module_registry import get_registry


class ModuleListView(ListView):
    """View to list all available modules and their status"""
    template_name = 'modular_engine/module_list.html'
    context_object_name = 'modules'

    def get_queryset(self):
        registry = get_registry()
        return registry.get_all_modules()


@require_POST
def install_module_view(request, module_id):
    """View to install a module"""
    registry = get_registry()

    success = registry.install_module(module_id)

    if success:
        messages.success(
            request, f"Module '{module_id}' installed successfully")
    else:
        messages.error(request, f"Failed to install module '{module_id}'")

    return redirect(reverse('modular_engine:module_list'))


@require_POST
def uninstall_module_view(request, module_id):
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
