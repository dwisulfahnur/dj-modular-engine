from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import User
from django.urls import path
from django.http import HttpResponse, Http404
from django.utils import timezone

import datetime
from unittest.mock import patch, MagicMock

from modular_engine.models import Module
from modular_engine.module_registry import ModuleRegistry, registry
from modular_engine.middleware import ModuleURLMiddleware


class ModuleModelTest(TestCase):
    """Tests for the Module model"""
    
    def setUp(self):
        self.module = Module.objects.create(
            name="Test Module",
            module_id="test_module",
            description="A test module",
            version="1.0.0",
            status="installed",
            install_date=timezone.now(),
        )
    
    def test_module_creation(self):
        """Test that a module can be created"""
        self.assertEqual(self.module.name, "Test Module")
        self.assertEqual(self.module.module_id, "test_module")
        self.assertEqual(self.module.version, "1.0.0")
        self.assertEqual(self.module.status, "installed")
        
    def test_module_str(self):
        """Test the string representation of a module"""
        self.assertEqual(str(self.module), "Test Module (test_module) - installed")


class ModuleRegistryTest(TestCase):
    """Tests for the ModuleRegistry class"""
    
    def setUp(self):
        self.registry = ModuleRegistry()
        
        # Create a test module in the database
        self.module = Module.objects.create(
            name="Test Module",
            module_id="test_module",
            description="A test module",
            version="1.0.0",
            status="installed",
            install_date=timezone.now(),
        )
        
        # Register a test module
        self.registry.register_module(
            module_id="test_module",
            name="Test Module",
            description="A test module",
            version="1.0.0",
            app_name="test_app",
            url_patterns=[]
        )
        
        # Register another module but don't install it
        self.registry.register_module(
            module_id="uninstalled_module",
            name="Uninstalled Module",
            description="An uninstalled module",
            version="1.0.0",
            app_name="test_app",
            url_patterns=[]
        )
        
        # Add the registered module to active modules
        self.registry.modules["test_module"] = self.registry.available_modules["test_module"]
    
    def test_register_module(self):
        """Test that a module can be registered"""
        self.assertIn("test_module", self.registry.available_modules)
        self.assertEqual(self.registry.available_modules["test_module"]["name"], "Test Module")
    
    def test_get_all_modules(self):
        """Test getting all modules"""
        modules = self.registry.get_all_modules()
        self.assertEqual(len(modules), 2)
        
        # Check that both modules are in the list
        module_ids = [m["module_id"] for m in modules]
        self.assertIn("test_module", module_ids)
        self.assertIn("uninstalled_module", module_ids)
    
    def test_get_active_modules(self):
        """Test getting active modules"""
        active_modules = self.registry.get_active_modules()
        self.assertEqual(len(active_modules), 1)
        self.assertIn("test_module", active_modules)
    
    def test_uninstall_module(self):
        """Test uninstalling a module"""
        with patch('engine.module_registry.clear_url_caches'):
            result = self.registry.uninstall_module("test_module")
            
            self.assertTrue(result)
            self.assertNotIn("test_module", self.registry.modules)
            
            # Check that the module status was updated in the database
            module = Module.objects.get(module_id="test_module")
            self.assertEqual(module.status, "not_installed")
    
    def test_uninstall_nonexistent_module(self):
        """Test uninstalling a module that doesn't exist"""
        result = self.registry.uninstall_module("nonexistent_module")
        self.assertFalse(result)
    
    def test_install_module(self):
        """Test installing a module"""
        # First, uninstall the module
        with patch('engine.module_registry.clear_url_caches'):
            self.registry.uninstall_module("test_module")
        
        # Now reinstall it
        with patch('engine.module_registry.clear_url_caches'):
            result = self.registry.install_module("test_module")
            
            self.assertTrue(result)
            self.assertIn("test_module", self.registry.modules)
            
            # Check that the module status was updated in the database
            module = Module.objects.get(module_id="test_module")
            self.assertEqual(module.status, "installed")
    
    def test_install_with_setup_function(self):
        """Test installing a module that has a setup function"""
        # Create a mock setup function
        mock_setup = MagicMock()
        
        # Register a new module with the setup function
        self.registry.register_module(
            module_id="setup_module",
            name="Setup Module",
            description="A module with a setup function",
            version="1.0.0",
            app_name="test_app",
            setup_func=mock_setup,
            url_patterns=[]
        )
        
        # Install the module
        with patch('engine.module_registry.clear_url_caches'):
            result = self.registry.install_module("setup_module")
            
            self.assertTrue(result)
            self.assertIn("setup_module", self.registry.modules)
            
            # Check that the setup function was called
            mock_setup.assert_called_once()
    
    def test_install_with_failing_setup_function(self):
        """Test installing a module with a failing setup function"""
        # Create a mock setup function that raises an exception
        mock_setup = MagicMock(side_effect=Exception("Setup failed"))
        
        # Register a new module with the failing setup function
        self.registry.register_module(
            module_id="failing_setup_module",
            name="Failing Setup Module",
            description="A module with a failing setup function",
            version="1.0.0",
            app_name="test_app",
            setup_func=mock_setup,
            url_patterns=[]
        )
        
        # Try to install the module
        with patch('engine.module_registry.clear_url_caches'):
            with patch('engine.module_registry.logger') as mock_logger:
                result = self.registry.install_module("failing_setup_module")
                
                self.assertFalse(result)
                self.assertNotIn("failing_setup_module", self.registry.modules)
                
                # Check that the error was logged
                mock_logger.error.assert_called_once()
    
    def test_upgrade_module(self):
        """Test upgrading a module"""
        # Update the version in the available_modules
        self.registry.available_modules["test_module"]["version"] = "1.1.0"
        
        # Check if upgrade is available
        self.assertTrue(self.registry.check_upgrade_available("test_module"))
        
        # Upgrade the module
        with patch('engine.module_registry.clear_url_caches'):
            result = self.registry.upgrade_module("test_module")
            
            self.assertTrue(result)
            
            # Check that the module version was updated in the database
            module = Module.objects.get(module_id="test_module")
            self.assertEqual(module.version, "1.1.0")
            self.assertEqual(module.status, "installed")


class ModuleViewsTest(TestCase):
    """Test the module views"""
    
    def setUp(self):
        """Set up the test"""
        self.client = Client()
        
        # Create a superuser
        self.user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='password'
        )
        
        # Log in the user
        self.client.login(username='admin', password='password')
        
    def test_module_list_view(self):
        """Test the module list view"""
        # Patch the registry get_all_modules method to return a predictable result
        with patch('engine.views.get_registry') as mock_get_registry:
            mock_registry = MagicMock()
            mock_registry.get_all_modules.return_value = [
                {
                    'module_id': 'test_module',
                    'name': 'Test Module',
                    'description': 'A test module',
                    'version': '1.0.0',
                    'status': 'installed',
                    'install_date': timezone.now(),
                    'update_date': None
                },
                {
                    'module_id': 'uninstalled_module',
                    'name': 'Uninstalled Module',
                    'description': 'An uninstalled module',
                    'version': '1.0.0',
                    'status': 'not_installed',
                    'install_date': None,
                    'update_date': None
                }
            ]
            mock_get_registry.return_value = mock_registry
            
            response = self.client.get(reverse('engine:module_list'))
            
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'engine/module_list.html')
            self.assertEqual(len(response.context['modules']), 2)
            
    def test_install_module_view(self):
        """Test the install module view"""
        with patch('engine.views.get_registry') as mock_get_registry:
            mock_registry = MagicMock()
            mock_registry.install_module.return_value = True
            mock_get_registry.return_value = mock_registry
            
            response = self.client.post(
                reverse('engine:install_module', kwargs={'module_id': 'uninstalled_module'})
            )
            
            self.assertEqual(response.status_code, 302)  # Redirect
            self.assertRedirects(response, reverse('engine:module_list'))
            
            # Check that the module was installed
            mock_registry.install_module.assert_called_once_with('uninstalled_module')
            
    def test_uninstall_module_view(self):
        """Test the uninstall module view"""
        with patch('engine.views.get_registry') as mock_get_registry:
            mock_registry = MagicMock()
            mock_registry.uninstall_module.return_value = True
            mock_get_registry.return_value = mock_registry
            
            response = self.client.post(
                reverse('engine:uninstall_module', kwargs={'module_id': 'test_module'})
            )
            
            self.assertEqual(response.status_code, 302)  # Redirect
            self.assertRedirects(response, reverse('engine:module_list'))
            
            # Check that the module was uninstalled
            mock_registry.uninstall_module.assert_called_once_with('test_module')
            
    def test_upgrade_module_view(self):
        """Test the upgrade module view"""
        with patch('engine.views.get_registry') as mock_get_registry:
            mock_registry = MagicMock()
            mock_registry.upgrade_module.return_value = True
            mock_get_registry.return_value = mock_registry
            
            response = self.client.post(
                reverse('engine:upgrade_module', kwargs={'module_id': 'test_module'})
            )
            
            self.assertEqual(response.status_code, 302)  # Redirect
            self.assertRedirects(response, reverse('engine:module_list'))
            
            # Check that the module was upgraded
            mock_registry.upgrade_module.assert_called_once_with('test_module')


class ModuleIntegrationTest(TestCase):
    """Tests for module integration with the main application"""
    
    def setUp(self):
        self.client = Client()
        
        # Create a superuser
        self.admin_user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="adminpassword"
        )
        
        # Log in the admin user
        self.client.login(username="admin", password="adminpassword")
        
        # Create a test module in the database with not_installed status
        self.module = Module.objects.create(
            name="Test Module",
            module_id="test_module",
            description="A test module",
            version="1.0.0",
            status="not_installed",
        )
        
        # Define URL patterns for the test module
        test_url_patterns = [
            path('test/', lambda request: HttpResponse("Test view"), name='test_view'),
        ]
        
        # Register the test module
        registry.register_module(
            module_id="test_module",
            name="Test Module",
            description="A test module",
            version="1.0.0",
            app_name="test_app",
            url_patterns=test_url_patterns
        )
    
    @patch('engine.module_registry.clear_url_caches')
    @patch('djmodular.urls.get_module_url_patterns')
    def test_url_routing_after_install(self, mock_get_patterns, mock_clear_caches):
        """Test that URLs are updated after installing a module"""
        # Create a test pattern that should be added when the module is installed
        test_pattern = path('test_module/test/', lambda request: HttpResponse("Test view"), name='test_view')
        mock_get_patterns.return_value = [test_pattern]
        
        # Install the module
        with self.settings(ROOT_URLCONF='djmodular.urls'):
            # Install the module
            registry.install_module("test_module")
            
            # Check that URL caches were cleared
            mock_clear_caches.assert_called()
    
    @patch('engine.module_registry.clear_url_caches')
    @patch('djmodular.urls.get_module_url_patterns')
    def test_url_routing_after_uninstall(self, mock_get_patterns, mock_clear_caches):
        """Test that URLs are updated after uninstalling a module"""
        # First, install the module
        registry.modules["test_module"] = registry.available_modules["test_module"]
        self.module.status = "installed"
        self.module.save()
        
        # Set up the mock to return an empty list after uninstall
        mock_get_patterns.return_value = []
        
        # Uninstall the module
        with self.settings(ROOT_URLCONF='djmodular.urls'):
            # Uninstall the module
            registry.uninstall_module("test_module")
            
            # Check that URL caches were cleared
            mock_clear_caches.assert_called()


class ModuleMiddlewareTest(TestCase):
    """Tests for the ModuleURLMiddleware"""
    
    def setUp(self):
        self.factory = RequestFactory()
        
        # Create a simple dummy view
        self.dummy_view = lambda request: HttpResponse("OK")
        
        # Create middleware instance
        self.middleware = ModuleURLMiddleware(self.dummy_view)
        
        # Create test modules in the database
        self.installed_module = Module.objects.create(
            name="Installed Module",
            module_id="installed_module",
            description="An installed module",
            version="1.0.0",
            status="installed",
            install_date=timezone.now(),
        )
        
        self.uninstalled_module = Module.objects.create(
            name="Uninstalled Module",
            module_id="uninstalled_module",
            description="An uninstalled module",
            version="1.0.0",
            status="not_installed",
        )
        
        # Register modules in the registry
        registry.register_module(
            module_id="installed_module",
            name="Installed Module",
            description="An installed module",
            version="1.0.0",
            app_name="test_app",
            url_patterns=[]
        )
        
        registry.register_module(
            module_id="uninstalled_module",
            name="Uninstalled Module",
            description="An uninstalled module",
            version="1.0.0",
            app_name="test_app",
            url_patterns=[]
        )
        
        # Add only the installed module to active modules
        registry.modules["installed_module"] = registry.available_modules["installed_module"]
    
    def test_middleware_allows_installed_module(self):
        """Test that the middleware allows access to installed modules"""
        request = self.factory.get('/installed_module/')
        
        # Should not raise an exception
        response = self.middleware(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"OK")
    
    def test_middleware_blocks_uninstalled_module(self):
        """Test that the middleware blocks access to uninstalled modules"""
        request = self.factory.get('/uninstalled_module/')
        
        # Should raise Http404
        with self.assertRaises(Http404):
            self.middleware(request)
    
    def test_middleware_allows_non_module_paths(self):
        """Test that the middleware allows access to non-module paths"""
        for path in ['/', '/admin/', '/module/']:
            request = self.factory.get(path)
            response = self.middleware(request)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content, b"OK")
