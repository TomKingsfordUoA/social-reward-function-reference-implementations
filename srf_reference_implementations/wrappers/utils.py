import contextlib
import importlib
import os
import sys


@contextlib.contextmanager
def manage_dependencies(pythonpaths, pymo_path):
    # Prepend paths to PYTHONPATH:
    for path in reversed(pythonpaths):
        sys.path.insert(0, path)

    pymo_modules = [
        os.path.splitext(filename)[0]
        for filename in os.listdir(pymo_path)
    ]
    pymo_modules = [f'pymo.{filename}' if filename != '__init__' else 'pymo'
                    for filename in pymo_modules
                    if filename != '__pycache__']
    pymo_modules_before = {
        mod_name: sys.modules[mod_name] if mod_name in sys.modules else None
        for mod_name in pymo_modules
    }
    for mod_name in pymo_modules:
        if mod_name in sys.modules:
            del sys.modules[mod_name]
    specs_and_modules = dict()
    for mod_name in pymo_modules:
        mod_name_split = mod_name.split('.')
        if len(mod_name_split) == 1:
            mod_filename = '__init__.py'
        elif len(mod_name_split) == 2:
            mod_filename = f'{mod_name_split[1]}.py'
        else:
            raise ValueError()

        pymo_data_spec = importlib.util.spec_from_file_location(mod_name, os.path.join(pymo_path, mod_filename))
        if pymo_data_spec is None:
            raise ImportError()
        pymo_mod = importlib.util.module_from_spec(pymo_data_spec)
        specs_and_modules[mod_name] = (pymo_data_spec, pymo_mod)
        sys.modules[mod_name] = pymo_mod
    importlib.invalidate_caches()
    globals()['pymo'] = sys.modules['pymo']
    for mod_name in pymo_modules:
        parent_module, _, child_module = mod_name.rpartition('.')
        if parent_module:
            setattr(sys.modules[parent_module], child_module, sys.modules[mod_name])
    modules_to_be_executed = set(specs_and_modules.keys())
    while len(modules_to_be_executed):
        modules_executed_this_loop = set()
        for mod_name in modules_to_be_executed:
            spec, mod = specs_and_modules[mod_name]
            try:
                spec.loader.exec_module(mod)
                modules_executed_this_loop.add(mod_name)
            except (ImportError, NameError):
                pass
        if modules_to_be_executed and not modules_executed_this_loop:  # prevent infinite loops
            raise ImportError()
        modules_to_be_executed -= modules_executed_this_loop
    importlib.invalidate_caches()

    # sanity check (Mirror is only present in the old pymo used by Yoon2018)
    import pymo.preprocessing
    pymo.preprocessing.Mirror()

    yield

    # Restore pymo modules
    for mod_name, mod in pymo_modules_before.items():
        if mod is None:
            continue
        sys.modules[mod_name] = pymo_modules_before[mod_name]
        importlib.invalidate_caches()
        __import__(mod_name)
    globals()['pymo'] = sys.modules['pymo']

    # Restore PYTHONPATH:
    for path in pythonpaths:
        sys.path.remove(path)
