"""
Lazy Import Utilities
Defers heavy imports until they're actually needed to improve startup time
"""
import importlib
from typing import Any, Optional
from functools import wraps


class LazyImport:
    """
    Lazy import wrapper that defers module loading until first use.

    Usage:
        # Instead of:
        import heavy_module
        result = heavy_module.some_function()

        # Use:
        heavy_module = LazyImport("heavy_module")
        result = heavy_module.some_function()

    The module won't be imported until you actually call some_function().
    """

    def __init__(self, module_name: str):
        self._module_name = module_name
        self._module: Optional[Any] = None

    def _load(self):
        """Load the module if not already loaded"""
        if self._module is None:
            self._module = importlib.import_module(self._module_name)
        return self._module

    def __getattr__(self, name: str) -> Any:
        """Lazy load module when accessing attributes"""
        module = self._load()
        return getattr(module, name)

    def __dir__(self):
        """Support dir() for inspecting the module"""
        module = self._load()
        return dir(module)


def lazy_import(module_name: str) -> LazyImport:
    """
    Create a lazy import wrapper.

    Args:
        module_name: Name of the module to import

    Returns:
        LazyImport wrapper

    Example:
        celery = lazy_import("celery")
        # celery module is not loaded yet

        @celery.task
        def my_task():
            pass
        # Now celery is loaded
    """
    return LazyImport(module_name)


def lazy_function(module_name: str, function_name: str):
    """
    Decorator to lazily import a module when a function is called.

    Args:
        module_name: Name of the module to import
        function_name: Name of the function to import from the module

    Usage:
        @lazy_function("heavy_module", "process_data")
        def process_data_wrapper(*args, **kwargs):
            # This will import heavy_module.process_data on first call
            pass

        # Or use directly:
        process = lazy_function("numpy", "array")
        result = process([1, 2, 3])  # numpy loaded here
    """
    def decorator(func):
        _cached_func = None

        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal _cached_func
            if _cached_func is None:
                module = importlib.import_module(module_name)
                _cached_func = getattr(module, function_name)
            return _cached_func(*args, **kwargs)

        return wrapper

    # If called without decorator
    if callable(module_name):
        return decorator(module_name)

    return decorator


class LazyModule:
    """
    Context manager for lazy imports within a specific scope.

    Usage:
        with LazyModule("pandas") as pd:
            df = pd.DataFrame({"a": [1, 2, 3]})
    """

    def __init__(self, module_name: str):
        self._module_name = module_name
        self._module = None

    def __enter__(self):
        if self._module is None:
            self._module = importlib.import_module(self._module_name)
        return self._module

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


# Pre-configured lazy imports for common heavy modules
celery_lazy = lazy_import("celery")
numpy_lazy = lazy_import("numpy")
pandas_lazy = lazy_import("pandas")


def import_celery():
    """Import Celery only when needed"""
    return importlib.import_module("celery")


def import_scanner(scanner_type: str):
    """
    Import scanner module only when needed.

    Args:
        scanner_type: Type of scanner (e.g., "nmap", "nuclei", "zap")

    Returns:
        Scanner module
    """
    scanner_map = {
        "nmap": "app.api.services.scanner",
        "nuclei": "app.services.nuclei_scanner",
        "zap": "app.services.zap_scanner",
    }

    module_name = scanner_map.get(scanner_type)
    if not module_name:
        raise ValueError(f"Unknown scanner type: {scanner_type}")

    return importlib.import_module(module_name)


def import_report_generator():
    """Import report generator only when needed"""
    return importlib.import_module("app.services.report_generator")


# Example usage in code:
# Instead of:
#   from celery import Celery
#   app = Celery()
#
# Use:
#   from app.core.lazy_import import import_celery
#   def create_celery_app():
#       Celery = import_celery().Celery
#       return Celery()