from django.core.management.base import BaseCommand, CommandError

import ebooks.ebook_parser as parsers

class Command(BaseCommand):
    help = 'Imports recipes from an ebook parsed via BookParser instance'

    def add_arguments(self, parser):
        parser.add_argument('ebook_location', type=str)
        parser.add_argument('parser', type=str)

    def handle(self, *args, **options):
        ebook_location = options['ebook_location']
        parser_name = options['parser']
        print(f'received args {args} and options: {ebook_location}')

        parser_klass = getattr(parsers, parser_name)
        parser = parser_klass(ebook_location)
        parser.parse_book()
        print('done!')

        # TODO:  need to use next stage parser to create models of current recipes