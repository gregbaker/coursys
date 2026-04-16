from django.core.management.base import BaseCommand
from django.apps import apps

from courselib.purge import PurgePolicy


def flatten(xss):  # from https://stackoverflow.com/a/952952
    return [x for xs in xss for x in xs]


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--actually-delete', action='store_true', default=False)
        parser.add_argument('--verbose', action='store_true', default=False)
    
    def handle(self, *args, **options):
        commit = options['actually_delete']
        model_classes = flatten(i.get_models() for i in apps.get_app_configs())
        purgeable = [c for c in model_classes if hasattr(c, 'purge_policy')]
        # TODO: does purgeable need to be topologically-sorted by foreign key references?

        for cls in purgeable:
            policy = getattr(cls, 'purge_policy')
            assert(isinstance(policy, PurgePolicy))

            try:
                qs = policy.purgeable_queryset(cls)
                print(f'Purging {qs.count()} instances of {cls.__name__}')
                if options['verbose']:
                    print(f"... {qs}")
                if commit:
                    qs.delete()

            except NotImplementedError:
                items = list(policy.purgeable_instances(cls))
                print(f'Purging {len(items)} instances of {cls.__name__}')
                if options['verbose']:
                    items = list(items)
                    print(f"... {items}")
                if commit:
                    for i in items:
                        i.delete()
