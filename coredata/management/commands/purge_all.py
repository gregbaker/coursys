import importlib
import inspect
from types import ModuleType
from django.core.management.base import BaseCommand
from django.apps import apps
from courselib.purge import DataPurger


def flatten(xss):  # from https://stackoverflow.com/a/952952
    return [x for xs in xss for x in xs]


def try_import(module_name: str) -> ModuleType | None:
    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError:
        return None


def is_purger_class(obj) -> bool:
    return inspect.isclass(obj) and issubclass(obj, DataPurger) and obj is not DataPurger


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
    
    def handle(self, *args, **options):
        # adapted from django-haystack utils/app_loading.py and utils/loading.py
        app_modules = (i.module for i in apps.get_app_configs())
        purge_module_names = (f'{app_mod.__name__}.purge' for app_mod in app_modules)
        purge_modules = (try_import(m) for m in purge_module_names)
        purgers = flatten(inspect.getmembers(mod, is_purger_class) for mod in purge_modules if mod is not None)
        
        for p in purgers:
            _, purger = p
            qs = purger().purge_queryset()
            print(qs)