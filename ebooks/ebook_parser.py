import inspect

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup

from api.individual_recipe_parser import GLASSWARE
from recipe_scrapers._utils import normalize_string


class RecipeParser:
    def __init__(self, element):
        self.entry = element
        self.entry_parent = element.parent

    @classmethod
    def find_all_possible(self, root):
        raise NotImplementedError("This should be implemented.")

    @property
    def garnish(self):
        return None

    @property
    def glass(self):
        return None

    @property
    def title(self):
        raise NotImplementedError("This should be implemented.")

    @property
    def ingredients(self):
        raise NotImplementedError("This should be implemented.")

    @property
    def instructions(self):
        raise NotImplementedError("This should be implemented.")

    def ratings(self):
        return None

    def reviews(self):
        return None

    def links(self):
        invalid_href = ('#', '')
        links_html = self.soup.findAll('a', href=True)

        return [
            link.attrs
            for link in links_html
            if link['href'] not in invalid_href
        ]

    def can_parse(self):
        return True if (self.ingredients and self.instructions) else False

    @staticmethod
    def find_any_glass(text):
        for glass in GLASSWARE:
            if glass in text.lower():
                return normalize_string(glass)
        return None


class BookParser:
    def __init__(self, file_location):
        self.book = epub.read_epub(file_location)

        self.title = self.book.get_metadata('DC', 'title')[0][0]

        self.html_gen = self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT)

        self.recipe_objects = []
        # self.parser = etree.XMLParser(recover=True, remove_comments=True)

    @classmethod
    def get_recipe_parsers(cls):
        return [cls_attribute for cls_attribute in cls.__dict__.values()
                if inspect.isclass(cls_attribute)]

    def parse_book(self):
        for html in self.html_gen:
            text = html.get_content()
            root = BeautifulSoup(text, 'html.parser')
            self.parse_recipes(root)

    def parse_recipes(self, item):
        raise NotImplementedError

# p=DeathAndCoParser('./ebooks/epub/deathco.epub')
# p.parse_book()
# p.recipe_objects[210].garnish

class DeathAndCoParser(BookParser):
    class DeathCoRecipeOne(RecipeParser):
        @classmethod
        def find_all_possible(cls, root):
            all_possible = root.find_all('p', {'class': 'box_subheader'})
            return [cls(element) for element in all_possible]

        @property
        def garnish(self):
            self.ingredients
            return self._garnish

        @property
        def glass(self):
            self.instructions
            return self.find_any_glass(self._instructions)

        @property
        def title(self):
            return self.entry.text

        @property
        def ingredients(self):
            vals = self.entry_parent.find('div', {'class': 'ingredients'}).find_all('p')
            rets = []
            for val in vals:
                if val.startswith('GARNISH:'):
                    self._garnish = normalize_string(val.text.split(':')[1].strip())
                else:
                    rets.append(normalize_string(val.text))
            return vals

        @property
        def instructions(self):
            if hasattr(self, '_instructions'):
                return self._instructions

            instructions = self.entry_parent.find_all('p', {'class': 'box_nonindent'})[-1].text
            self._instructions = normalize_string(instructions)
            return self._instructions

    class DeathCoRecipeTwo(RecipeParser):
        @classmethod
        def find_all_possible(cls, root):
            all_possible = root.find_all('h3', {'class': 'recipe_subtitle1'})
            return [cls(element) for element in all_possible]

        @property
        def garnish(self):
            if hasattr(self, '_garnish'):
                return self._garnish

            self.ingredients
            return self._garnish

        @property
        def glass(self):
            return self.find_any_glass(self.instructions)

        @property
        def title(self):
            return self.entry.text

        @property
        def ingredients(self):
            if hasattr(self, '_ingredients'):
                return self._ingredients

            current = self.entry

            while True:
                try:
                    if current['class'][0] == 'ingredients':
                        break
                except TypeError:
                    pass

                current = current.next_sibling

            ingredients = current.find_all('p', {'class': 'IL_item'})
            rets = []

            for val in ingredients:
                if val.text.startswith('GARNISH:'):
                    self._garnish = normalize_string(val.text.split(':')[1].strip())
                else:
                    rets.append(normalize_string(val.text))
            self._current_at_ingredients = current
            self._ingredients = rets
            return rets

        @property
        def instructions(self):
            if hasattr(self, '_instructions'):
                return self._instructions
            self.ingredients
            instructions = self._current_at_ingredients.findNext('p', {'class': 'sub_method'}).text
            self._instructions = normalize_string(instructions)
            return self._instructions

    def parse_recipes(self, root):
        for parser in self.get_recipe_parsers():
            recipes = parser.find_all_possible(root)
            self.recipe_objects += recipes
        return self.recipe_objects


