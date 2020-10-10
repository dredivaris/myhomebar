from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Combines ingredients that are essentially the same and properly links recipes with' \
           'them'


    def handle(self, *args, **options):
        # TODO add combine code here
        pass