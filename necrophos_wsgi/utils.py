from importlib import import_module


def ensure_bytes(value):
    if isinstance(value, str):
        value = value.encode('utf-8')

    return value


def import_object(path):
    module_path, obj_name = path.split(':')

    module = import_module(module_path)
    return getattr(module, obj_name)
