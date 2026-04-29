import importlib
import pkgutil
from pathlib import Path

from flask import Blueprint


def register_blueprints(app):
    """Auto-discover and register all Blueprints in openspade/api/*.py.

    Convention:
        - Each module in this package can define one or more Blueprint instances.
        - URL prefix defaults to ``/api/{module_name}``.
        - To override, define a module-level ``url_prefix`` variable.
    """
    package_path = Path(__file__).parent
    package_name = 'openspade.api'

    for importer, module_name, is_pkg in pkgutil.iter_modules([str(package_path)]):
        try:
            module = importlib.import_module(f'{package_name}.{module_name}')
        except Exception as e:
            print(f'[api] Failed to load module "{module_name}": {e}')
            continue

        # Check if the module defines a custom url_prefix
        default_prefix = f'/api/{module_name}'
        module_prefix = getattr(module, 'url_prefix', None)

        for attr_name in dir(module):
            obj = getattr(module, attr_name)
            if isinstance(obj, Blueprint):
                prefix = module_prefix or default_prefix
                app.register_blueprint(obj, url_prefix=prefix)
                print(f'[api] Registered blueprint "{obj.name}" at {prefix}')
