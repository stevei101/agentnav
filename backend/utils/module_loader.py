"""
Utility helpers for safely importing backend modules during runtime.

These helpers let us simulate missing optional dependencies in tests without
breaking the Python import machinery (e.g. when tests monkeypatch
``builtins.__import__``).
"""

from __future__ import annotations

import builtins
import sys
from types import ModuleType
from typing import Iterable, Tuple

_ORIGINAL_IMPORT = builtins.__import__


def _import_module(module_name: str) -> ModuleType:
    """
    Import a module using the original ``__import__`` implementation.

    Args:
        module_name: The fully-qualified module name to import.

    Returns:
        Imported module object.

    Raises:
        ImportError: If the module cannot be imported.
    """
    try:
        module = _ORIGINAL_IMPORT(module_name, globals(), locals(), [], 0)
    except ImportError as exc:  # pragma: no cover - passthrough for clarity
        raise exc

    if not isinstance(module, ModuleType):  # pragma: no cover - defensive guard
        raise ImportError(f"Failed to import module '{module_name}'")

    sys.modules[module_name] = module
    return module


def safe_import_module(module_name: str) -> ModuleType:
    """
    Safely import a module even when ``builtins.__import__`` is monkeypatched.

    This checks ``sys.modules`` first. If the entry exists and is ``None``, the
    caller is intentionally simulating an import failure (e.g. our health
    endpoint tests). In that case we raise ``ImportError`` immediately so the
    caller can handle the degraded state without touching the patched import
    hook. Otherwise we fall back to the cached module or import it using the
    original interpreter hook.
    """
    if module_name in sys.modules:
        cached = sys.modules[module_name]
        if cached is None:
            raise ImportError(f"No module named '{module_name}'")
        if isinstance(cached, ModuleType):
            return cached

    return _import_module(module_name)


def load_attributes(module_name: str, attributes: Iterable[str]) -> Tuple:
    """
    Load specific attributes from a module using :func:`safe_import_module`.

    Args:
        module_name: Module to import.
        attributes: Iterable of attribute names to retrieve from the module.

    Returns:
        Tuple containing the requested attributes in order.
    """
    module = safe_import_module(module_name)
    return tuple(getattr(module, attr) for attr in attributes)

