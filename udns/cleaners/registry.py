"""
Registry system for dynamically loading and managing cleaning plugins.
"""

import importlib
import inspect
import pkgutil
from typing import Any, Dict, List, Optional, Type, Set
from pathlib import Path

from .base import BaseCleaner, CleaningContext, CleanResult


class CleaningPluginRegistry:
    """Registry for dynamically loaded cleaning plugins."""
    
    def __init__(self):
        """Initialize the registry."""
        self.plugins: Dict[str, Type[BaseCleaner]] = {}
        self.instances: Dict[str, BaseCleaner] = {}
        self.builtin_plugins: Set[str] = set()
        self.load_builtin_plugins()
    
    def load_builtin_plugins(self):
        """Load all built-in cleaning plugins."""
        # Import all modules in the cleaners package
        package_path = Path(__file__).parent
        for _, module_name, _ in pkgutil.iter_modules([str(package_path)]):
            if module_name not in ['base', 'pipeline', 'registry']:
                try:
                    module = importlib.import_module(f".{module_name}", package="udns.cleaners")
                    self._register_module_plugins(module, builtin=True)
                except ImportError as e:
                    print(f"Warning: Could not import cleaner module {module_name}: {e}")
    
    def _register_module_plugins(self, module: Any, builtin: bool = False):
        """Register all cleaner classes from a module."""
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseCleaner) and 
                obj is not BaseCleaner):
                
                # Register the plugin
                self.register_plugin(obj.__name__, obj)
                
                if builtin:
                    self.builtin_plugins.add(obj.__name__)
    
    def register_plugin(self, name: str, plugin_class: Type[BaseCleaner]):
        """
        Register a new cleaning plugin.
        
        Args:
            name: Unique name for the plugin
            plugin_class: Class implementing BaseCleaner
        """
        if not issubclass(plugin_class, BaseCleaner):
            raise ValueError(f"Plugin {name} must inherit from BaseCleaner")
        
        # Allow re-registration of built-in plugins (ignore duplicates)
        if name in self.plugins and name not in self.builtin_plugins:
            raise ValueError(f"Plugin {name} is already registered")
        
        self.plugins[name] = plugin_class
        # Clear any existing instance
        self.instances.pop(name, None)
    
    def unregister_plugin(self, name: str):
        """
        Unregister a cleaning plugin.
        
        Args:
            name: Name of the plugin to unregister
        """
        if name in self.builtin_plugins:
            raise ValueError(f"Cannot unregister built-in plugin {name}")
        
        self.plugins.pop(name, None)
        self.instances.pop(name, None)
    
    def get_plugin(self, name: str) -> Optional[BaseCleaner]:
        """
        Get a plugin instance by name.
        
        Args:
            name: Name of the plugin
            
        Returns:
            Plugin instance or None if not found
        """
        if name not in self.plugins:
            return None
        
        # Return cached instance if available
        if name in self.instances:
            return self.instances[name]
        
        # Create new instance
        try:
            instance = self.plugins[name]()
            self.instances[name] = instance
            return instance
        except Exception as e:
            print(f"Error creating instance of plugin {name}: {e}")
            return None
    
    def get_plugin_class(self, name: str) -> Optional[Type[BaseCleaner]]:
        """
        Get a plugin class by name.
        
        Args:
            name: Name of the plugin
            
        Returns:
            Plugin class or None if not found
        """
        return self.plugins.get(name)
    
    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all registered plugins.
        
        Returns:
            List of plugin information dictionaries
        """
        plugins_info = []
        for name, plugin_class in self.plugins.items():
            try:
                instance = self.get_plugin(name)
                plugins_info.append({
                    "name": name,
                    "class": plugin_class.__name__,
                    "module": plugin_class.__module__,
                    "version": instance.version if instance else "unknown",
                    "enabled": instance.enabled if instance else False,
                    "builtin": name in self.builtin_plugins,
                    "configurable": len(plugin_class().validate_config()) > 0
                })
            except Exception as e:
                plugins_info.append({
                    "name": name,
                    "class": plugin_class.__name__,
                    "module": plugin_class.__module__,
                    "error": str(e),
                    "builtin": name in self.builtin_plugins
                })
        
        return plugins_info
    
    def get_builtin_plugins(self) -> List[str]:
        """
        Get list of built-in plugin names.
        
        Returns:
            List of built-in plugin names
        """
        return list(self.builtin_plugins)
    
    def get_custom_plugins(self) -> List[str]:
        """
        Get list of custom plugin names.
        
        Returns:
            List of custom plugin names
        """
        return [name for name in self.plugins.keys() if name not in self.builtin_plugins]
    
    def load_plugin_from_file(self, file_path: str, plugin_name: Optional[str] = None):
        """
        Load a plugin from a Python file.
        
        Args:
            file_path: Path to the Python file containing the plugin
            plugin_name: Optional name for the plugin (defaults to class name)
        """
        spec = importlib.util.spec_from_file_location("custom_plugin", file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load plugin from {file_path}")
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Find BaseCleaner subclasses in the module
        cleaner_classes = []
        for name, obj in inspect.getmembers(module):
            if (inspect.isclass(obj) and 
                issubclass(obj, BaseCleaner) and 
                obj is not BaseCleaner):
                cleaner_classes.append(obj)
        
        if not cleaner_classes:
            raise ValueError(f"No BaseCleaner subclasses found in {file_path}")
        
        # Register all found cleaners
        for cleaner_class in cleaner_classes:
            name = plugin_name or cleaner_class.__name__
            self.register_plugin(name, cleaner_class)
    
    def load_plugins_from_directory(self, directory: str, pattern: str = "*_cleaner.py"):
        """
        Load all plugins from a directory.
        
        Args:
            directory: Directory containing plugin files
            pattern: File pattern to match (default: "*_cleaner.py")
        """
        from pathlib import Path
        import glob
        
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory {directory} does not exist")
        
        # Find all matching files
        for file_path in glob.glob(str(dir_path / pattern)):
            try:
                self.load_plugin_from_file(file_path)
            except Exception as e:
                print(f"Warning: Could not load plugin from {file_path}: {e}")
    
    def create_pipeline(self, plugin_names: List[str], **kwargs) -> 'CleaningPipeline':
        """
        Create a cleaning pipeline from a list of plugin names.
        
        Args:
            plugin_names: List of plugin names to include in pipeline
            **kwargs: Additional arguments for pipeline creation
            
        Returns:
            CleaningPipeline instance
        """
        from .pipeline import CleaningPipeline
        
        cleaners = []
        for name in plugin_names:
            cleaner = self.get_plugin(name)
            if cleaner:
                cleaners.append(cleaner)
            else:
                raise ValueError(f"Plugin {name} not found in registry")
        
        return CleaningPipeline(cleaners, **kwargs)
    
    def validate_plugin(self, name: str) -> List[str]:
        """
        Validate a plugin configuration.
        
        Args:
            name: Name of the plugin to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        plugin = self.get_plugin(name)
        if not plugin:
            return [f"Plugin {name} not found"]
        
        return plugin.validate_config()
    
    def configure_plugin(self, name: str, **kwargs):
        """
        Configure a plugin.
        
        Args:
            name: Name of the plugin to configure
            **kwargs: Configuration parameters
        """
        plugin = self.get_plugin(name)
        if not plugin:
            raise ValueError(f"Plugin {name} not found")
        
        plugin.configure(**kwargs)
    
    def enable_plugin(self, name: str, enabled: bool = True):
        """
        Enable or disable a plugin.
        
        Args:
            name: Name of the plugin
            enabled: Whether to enable the plugin
        """
        plugin = self.get_plugin(name)
        if not plugin:
            raise ValueError(f"Plugin {name} not found")
        
        plugin.enabled = enabled
    
    def get_plugin_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a plugin.
        
        Args:
            name: Name of the plugin
            
        Returns:
            Plugin information dictionary or None if not found
        """
        plugin_class = self.plugins.get(name)
        if not plugin_class:
            return None
        
        try:
            instance = self.get_plugin(name)
            return {
                "name": name,
                "class": plugin_class.__name__,
                "module": plugin_class.__module__,
                "version": instance.version if instance else "unknown",
                "enabled": instance.enabled if instance else False,
                "builtin": name in self.builtin_plugins,
                "config": instance.config if instance else {},
                "config_errors": instance.validate_config() if instance else [],
                "can_handle": "All data types",  # Could be more specific
                "description": plugin_class.__doc__ or "No description available"
            }
        except Exception as e:
            return {
                "name": name,
                "class": plugin_class.__name__,
                "module": plugin_class.__module__,
                "error": str(e),
                "builtin": name in self.builtin_plugins
            }
    
    def clear_instances(self):
        """Clear all cached plugin instances."""
        self.instances.clear()
    
    def reload_plugin(self, name: str):
        """
        Reload a plugin (clear instance and recreate).
        
        Args:
            name: Name of the plugin to reload
        """
        if name in self.builtin_plugins:
            raise ValueError(f"Cannot reload built-in plugin {name}")
        
        # Clear instance
        self.instances.pop(name, None)
        
        # Get new instance
        self.get_plugin(name)
    
    def export_config(self) -> Dict[str, Any]:
        """
        Export current plugin configuration.
        
        Returns:
            Dictionary containing plugin configuration
        """
        config = {
            "plugins": {},
            "pipeline": []
        }
        
        for name, plugin_class in self.plugins.items():
            instance = self.get_plugin(name)
            if instance:
                config["plugins"][name] = {
                    "enabled": instance.enabled,
                    "config": instance.config
                }
        
        return config
    
    def import_config(self, config: Dict[str, Any]):
        """
        Import plugin configuration.
        
        Args:
            config: Configuration dictionary
        """
        plugins_config = config.get("plugins", {})
        
        for name, plugin_config in plugins_config.items():
            if name in self.plugins:
                self.configure_plugin(name, **plugin_config.get("config", {}))
                self.enable_plugin(name, plugin_config.get("enabled", True))
    
    def __len__(self) -> int:
        """Get number of registered plugins."""
        return len(self.plugins)
    
    def __contains__(self, name: str) -> bool:
        """Check if plugin is registered."""
        return name in self.plugins
    
    def __iter__(self):
        """Iterate over plugin names."""
        return iter(self.plugins.keys())
    
    def __str__(self) -> str:
        """String representation of registry."""
        builtin_count = len(self.builtin_plugins)
        custom_count = len(self.plugins) - builtin_count
        return f"CleaningPluginRegistry(builtin={builtin_count}, custom={custom_count})"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"CleaningPluginRegistry(plugins={len(self.plugins)}, "
                f"builtin={len(self.builtin_plugins)}, "
                f"custom={len(self.plugins) - len(self.builtin_plugins)})")


# Global registry instance
_global_registry = None


def get_global_registry() -> CleaningPluginRegistry:
    """Get the global plugin registry instance."""
    global _global_registry
    if _global_registry is None:
        _global_registry = CleaningPluginRegistry()
    return _global_registry


def register_plugin(name: str, plugin_class: Type[BaseCleaner]):
    """Register a plugin with the global registry."""
    get_global_registry().register_plugin(name, plugin_class)


def get_plugin(name: str) -> Optional[BaseCleaner]:
    """Get a plugin instance from the global registry."""
    return get_global_registry().get_plugin(name)


def list_plugins() -> List[Dict[str, Any]]:
    """List all plugins in the global registry."""
    return get_global_registry().list_plugins()


def create_pipeline(plugin_names: List[str], **kwargs) -> 'CleaningPipeline':
    """Create a pipeline from the global registry."""
    return get_global_registry().create_pipeline(plugin_names, **kwargs)