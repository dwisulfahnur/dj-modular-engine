from django.urls import path, include

urlpatterns = [
    path('modular-engine/', include('modular_engine.urls', namespace='modular_engine')),
    # Add authentication URLs for the logout view
    path('accounts/', include('django.contrib.auth.urls')),
]
