from django.core.management.base import BaseCommand
from django.apps import apps

from courselib.purge import PurgePolicy


def flatten(xss):  # from https://stackoverflow.com/a/952952
    return [x for xs in xss for x in xs]


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
    
    def handle(self, *args, **options):
        commit = not options['dry_run']
        model_classes = flatten(i.get_models() for i in apps.get_app_configs())
        purgeable = [c for c in model_classes if hasattr(c, 'purge_policy')]

        for cls in purgeable:
            policy = getattr(cls, 'purge_policy')
            assert(isinstance(policy, PurgePolicy))

            try:
                qs = policy.purgeable_queryset(cls)
                print(f'Purging {qs.count()} instances of {cls.__name__}')
                if commit:
                    qs.delete()

            except NotImplementedError:
                items = list(policy.purgeable_instances(cls))
                print(f'Purging {len(items)} instances of {cls.__name__}')
                for i in items:
                    if commit:
                        i.delete()
