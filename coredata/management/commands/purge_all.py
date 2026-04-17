from django.core.management.base import BaseCommand
from courselib.purge import purge_all


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--actually-delete', '-d', action='store_true', default=False)
    
    def handle(self, *args, **options):
        purge_all(verbosity=options['verbosity'], commit=options['actually_delete'])
        

