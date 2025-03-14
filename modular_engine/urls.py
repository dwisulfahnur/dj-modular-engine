from django.urls import path
from modular_engine import views

app_name = 'modular_engine'

urlpatterns = [
    path('', views.ModuleListView.as_view(), name='module_list'),
    path('install/<str:module_id>/', views.install_module_view, name='install_module'),
    path('uninstall/<str:module_id>/', views.uninstall_module_view, name='uninstall_module'),
    path('upgrade/<str:module_id>/', views.upgrade_module_view, name='upgrade_module'),
] 
