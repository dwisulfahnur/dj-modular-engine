from django.db import models

MODULE_STATUS_CHOICES = [
    ('installed', 'Installed'),
    ('not_installed', 'Not Installed'),
    ('upgrade_available', 'Upgrade Available'),
]

class Module(models.Model):
    """Model for storing installed modules and their status"""
    module_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    version = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=MODULE_STATUS_CHOICES, default='not_installed')
    install_date = models.DateTimeField(null=True, blank=True)
    update_date = models.DateTimeField(null=True, blank=True)
    base_path = models.CharField(max_length=100, blank=True, help_text="Custom base path for module URLs (empty to use module_id)")
    
    def __str__(self):
        return f"{self.name} ({self.module_id}) - {self.status}"
    
    def get_url_path(self):
        """Return the base path for the module's URL patterns"""
        return self.base_path if self.base_path else self.module_id
