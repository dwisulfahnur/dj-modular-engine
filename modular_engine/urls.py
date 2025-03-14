from django.urls import path
from modular_engine import views

app_name = 'modular_engine'

urlpatterns = [
    path('', views.ModuleListView.as_view(), name='module_list'),
    path('install/<str:module_id>/', views.install_module, name='install_module'),
    path('uninstall/<str:module_id>/', views.uninstall_module, name='uninstall_module'),
    path('upgrade/<str:module_id>/', views.upgrade_module_view, name='upgrade_module'),
    path('update-path/<str:module_id>/', views.update_module_path, name='update_module_path'),
    path('reload-urls/', views.reload_urls, name='reload_urls'),
] 
