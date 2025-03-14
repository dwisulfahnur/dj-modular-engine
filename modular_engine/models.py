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
    
    def __str__(self):
        return f"{self.name} ({self.module_id}) - {self.status}"
