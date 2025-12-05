"""
Adapter registry for managing and discovering adapters.
"""

from typing import Optional, Type

from beta_team.sdk.core.base import BaseAdapter, SoftwareType


class AdapterRegistry:
    """
    Registry for managing available adapters.

    This class provides a central location for registering and discovering
    adapters for different software types.
    """

    _adapters: dict[str, Type[BaseAdapter]] = {}
    _instances: dict[str, BaseAdapter] = {}

    @classmethod
    def register(cls, adapter_class: Type[BaseAdapter], name: Optional[str] = None) -> None:
        """
        Register an adapter class.

        Args:
            adapter_class: The adapter class to register.
            name: Optional name override; defaults to class name.
        """
        adapter_name = name or adapter_class.__name__
        cls._adapters[adapter_name] = adapter_class

    @classmethod
    def get_adapter_class(cls, name: str) -> Optional[Type[BaseAdapter]]:
        """
        Get an adapter class by name.

        Args:
            name: Name of the adapter.

        Returns:
            The adapter class, or None if not found.
        """
        return cls._adapters.get(name)

    @classmethod
    def create_adapter(cls, name: str, **kwargs) -> Optional[BaseAdapter]:
        """
        Create an instance of an adapter.

        Args:
            name: Name of the adapter to create.
            **kwargs: Arguments to pass to the adapter constructor.

        Returns:
            An instance of the adapter, or None if not found.
        """
        adapter_class = cls._adapters.get(name)
        if adapter_class:
            return adapter_class(**kwargs)
        return None

    @classmethod
    def list_adapters(cls) -> list[str]:
        """
        List all registered adapter names.

        Returns:
            List of adapter names.
        """
        return list(cls._adapters.keys())

    @classmethod
    def list_adapters_by_type(cls, software_type: SoftwareType) -> list[str]:
        """
        List adapters that handle a specific software type.

        Args:
            software_type: The software type to filter by.

        Returns:
            List of adapter names for the given type.
        """
        results = []
        for name, adapter_class in cls._adapters.items():
            # Create a temporary instance to check software type
            # This is a simple approach; could be optimized with metadata
            try:
                # Check class attribute if available
                if hasattr(adapter_class, 'SOFTWARE_TYPE'):
                    if adapter_class.SOFTWARE_TYPE == software_type:
                        results.append(name)
            except Exception:
                # Adapter class may have issues - skip it and continue with others
                pass
        return results

    @classmethod
    def clear(cls) -> None:
        """Clear all registered adapters."""
        cls._adapters.clear()
        cls._instances.clear()
