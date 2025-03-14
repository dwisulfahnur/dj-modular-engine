from django.urls import path
from modular_engine import views

app_name = 'modular_engine'

urlpatterns = [
    path('module/', views.ModuleListView.as_view(), name='module_list'),
    path('module/install/<str:module_id>/', views.install_module, name='install_module'),
    path('module/uninstall/<str:module_id>/', views.uninstall_module, name='uninstall_module'),
    path('module/upgrade/<str:module_id>/', views.upgrade_module, name='upgrade_module'),
] 
