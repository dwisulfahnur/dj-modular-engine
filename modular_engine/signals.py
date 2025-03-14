import logging
import time
import os
from django.dispatch import Signal, receiver
from django.urls import clear_url_caches
from django.core.signals import request_finished
from django.db.models.signals import post_migrate
from django.conf import settings

# Define signals
module_path_changed = Signal()

logger = logging.getLogger(__name__)

# Global timestamp to track last URL modification
LAST_URL_CHANGE = 0

def mark_urls_changed():
    """Mark that URLs have changed by updating the timestamp"""
    global LAST_URL_CHANGE
    LAST_URL_CHANGE = time.time()
    
    # Also store timestamp in a file for cross-process invalidation
    timestamp_file = get_timestamp_file_path()
    try:
        with open(timestamp_file, 'w') as f:
            f.write(str(LAST_URL_CHANGE))
    except Exception as e:
        logger.error(f"Error writing URL change timestamp: {e}")

def get_timestamp_file_path():
    """Get the path to the URL timestamp file"""
    base_dir = getattr(settings, 'BASE_DIR', None)
    if base_dir:
        return os.path.join(base_dir, '.url_timestamp')
    return '/tmp/.django_url_timestamp'

def get_last_url_change():
    """Get the timestamp of the last URL change"""
    global LAST_URL_CHANGE
    
    # Check if there's a newer timestamp in the file
    timestamp_file = get_timestamp_file_path()
    try:
        if os.path.exists(timestamp_file):
            with open(timestamp_file, 'r') as f:
                file_timestamp = float(f.read().strip())
                if file_timestamp > LAST_URL_CHANGE:
                    LAST_URL_CHANGE = file_timestamp
    except Exception as e:
        logger.error(f"Error reading URL change timestamp: {e}")
        
    return LAST_URL_CHANGE

def force_reload_urls():
    """Force Django to reload all URL configurations"""
    try:
        # Clear all URL caches
        clear_url_caches()
        
        # Reset the URLconf for the current thread
        from django.urls import set_urlconf
        set_urlconf(None)
        
        # Reload main URLconf module
        import sys
        import importlib
        if hasattr(settings, 'ROOT_URLCONF'):
            urlconf = settings.ROOT_URLCONF
            if urlconf in sys.modules:
                importlib.reload(sys.modules[urlconf])
                
        # Additionally, check for and reload other URL modules
        for name in list(sys.modules.keys()):
            if 'urls' in name and not name.startswith('django.'):
                try:
                    module = sys.modules[name]
                    importlib.reload(module)
                except:
                    pass
                    
        # Mark that we've changed the URLs
        mark_urls_changed()
        
        logger.info("Successfully forced URL configuration reload")
    except Exception as e:
        logger.error(f"Error forcing URL reload: {e}")

@receiver(module_path_changed)
def clear_url_caches_on_module_path_change(sender, **kwargs):
    """
    Signal handler that clears URL caches when a module path is changed
    """
    logger.debug("Clearing URL caches due to module path change")
    
    # Force a complete URL reload
    force_reload_urls()

@receiver(post_migrate)
def clear_url_caches_after_migrate(sender, **kwargs):
    """
    Signal handler that clears URL caches after migrations are applied
    This ensures that any model changes affecting URL patterns are reflected
    """
    if sender.name == 'modular_engine':
        logger.debug("Clearing URL caches after migrations")
        force_reload_urls() 