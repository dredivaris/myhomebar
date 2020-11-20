from collections import Iterable
from string import capwords

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from api.individual_recipe_parser import INGREDIENT_PARSER, JUICE_OF_PARSER, \
    ALTERNATIVE_UNIT_LOCATION_PARSER
from api.models import Recipe, Ingredient, Unit, Quantity, RecipeIngredient, IngredientMapping, \
    IngredientToIngredient


class RecipeValidator(object):
    def __init__(self, **kwargs):
        self.recipe_raw = kwargs
        self.recipe = None

    def validate(self):
        # print('proc ingredients')
        self.ingredients = self.process_ingredients()
        # print('proc type')
        self.recipe_type = self.process_type()
        self.process_garnish()
        self.process_rating()

    def save(self):
        self.recipe_raw['name'] = capwords(self.recipe_raw['name'])
        self.recipe = Recipe(**self.recipe_raw)

        self.recipe.owner = self.user
        # print(f'Checking dup for {self.recipe.owner}, {self.recipe.name}, {self.recipe.source} found num: {Recipe.objects.filter(owner=self.recipe.owner, name=self.recipe.name, source=self.recipe.source).count()}')
        if Recipe.objects.filter(owner=self.recipe.owner,
                                 name=self.recipe.name, source=self.recipe.source).count() == 0:
            self.recipe.save()
            for ingredient in self.ingredients:
                self.save_and_add_ingredient(ingredient)

            self.save_and_add_garnish()
        else:
            print(f'duplicate found for {self.recipe.name}')

    def update(self):
        self.recipe_raw['name'] = capwords(self.recipe_raw['name'])
        # self.recipe = Recipe(**self.recipe_raw)

        recipe_id = self.recipe_raw.pop('id')
        Recipe.objects.filter(id=recipe_id).update(**self.recipe_raw)
        self.recipe = Recipe.objects.get(id=recipe_id)

        # self.recipe.owner = self.user
        # print(f'Checking dup for {self.recipe.owner}, {self.recipe.name}, {self.recipe.source} found num: {Recipe.objects.filter(owner=self.recipe.owner, name=self.recipe.name, source=self.recipe.source).count()}')
        # self.recipe.save()
        RecipeIngredient.objects.filter(beverage=self.recipe).delete()

        for ingredient in self.ingredients:
            self.save_and_add_ingredient(ingredient)
        self.save_and_add_garnish(update=True)

    def with_user(self, user):
        self.user = user

    def process_ingredients(self):
        from api.domain import clean_extras
        ingredients = []
        if 'ingredients' not in self.recipe_raw:
            ingredients_raw = []
        elif isinstance(self.recipe_raw['ingredients'], Iterable) \
                and type(self.recipe_raw['ingredients']) is not str:
            ingredients_raw = self.recipe_raw['ingredients']
        else:
            ingredient_text = self.recipe_raw['ingredients']
            ingredients_raw = ingredient_text.splitlines()

        for raw_ingredient in ingredients_raw:
            if type(raw_ingredient) is dict:
                ingredients.append(raw_ingredient)
            else:
                cleaned_text = raw_ingredient.strip()
                # probably should be refactored to use ingreedy.
                cleaned_text, extras = clean_extras(cleaned_text)
                match = INGREDIENT_PARSER.match(cleaned_text)
                if not match:
                    match = JUICE_OF_PARSER.match(cleaned_text)
                    if not match:
                        ingredient = {
                            'ingredient': cleaned_text
                        }
                    else:
                        ingredient = {
                            'amount': match.group(1),
                            'ingredient': match.group(2) + ' juice',
                        }
                    match = ALTERNATIVE_UNIT_LOCATION_PARSER.match(cleaned_text)
                    if match:
                        ingredient['amount'] = match.group(1)
                        ingredient['unit'] = match.group(2)
                else:
                    ingredient = {
                        'amount': match.group(1),
                        'unit': match.group(7),
                        'ingredient': match.group(8).strip(),
                        'scant': '-' in extras,
                        'generous': '+' in extras,
                    }
                ingredients.append(ingredient)

        self.recipe_raw.pop('ingredients', None)
        return ingredients

    def process_type(self):
        recipe_type = self.recipe_raw['recipe_type']
        if recipe_type not in {recipe_type[0] for recipe_type in Recipe.TYPES}:
            raise GraphQLError('Invalid recipe type.')
        self.recipe_raw.pop('recipe_type')
        return recipe_type

    def process_garnish(self):
        # todo: we want to support multiple garnishes in the future and garnish units
        try:
            garnish = self.recipe_raw['garnish'] and self.recipe_raw['garnish'].strip()
        except KeyError:
            return
        except AttributeError:
            return
        if garnish:
            self.garnish = garnish
        self.recipe_raw.pop('garnish')

    def process_rating(self):
        if not self.recipe_raw.get('rating_set'):
            self.rating = self.recipe_raw.get('rating', None)
        # TODO: is this right?
        self.recipe_raw.pop('rating_set', None)

    def save_and_add_ingredient(self, ingredient):
        # todo: change owner to current owner; think this is already true?
        unit = None
        print(f'creating for ingredient {ingredient}, {ingredient.get("unit", None)}')
        if ingredient.get('unit', None):
            _type = ingredient.get('type', None)
            unit, _ = Unit.objects.get_or_create(name=ingredient['unit'].lower(), owner=self.user)
            if not unit.type and _type:
                unit.type = _type
                unit.save()
        try:
            print(f'  with quantity {ingredient["amount"]} and unit: {unit}')
            quantity = Quantity.create_quantity(ingredient['amount'], unit=unit,
                                                scant=ingredient.get('scant', False),
                                                generous=ingredient.get('generous', False))
        except KeyError:
            print('  hit key error creating quantity')
            quantity = None
        ingredient_instance = None
        try:
            if len(ingredient['ingredient'].split(',')) == 2:
                base_ingredient, specific_ingredient = [i.strip() for i in
                                                        ingredient['ingredient'].split(',')]
                base, created = Ingredient.objects.get_or_create(name=capwords(base_ingredient),
                                                                 owner=self.user)
                print(f'setup base ingredient {base}, created: {created}')
                ingredient_instance, created = Ingredient.objects.get_or_create(
                    name=capwords(' '.join((specific_ingredient, base_ingredient))),
                    owner=self.user)
                try:
                    IngredientToIngredient.objects.get_or_create(child=ingredient_instance,
                                                                 parent_id=base.id)
                except IngredientToIngredient.MultipleObjectsReturned:
                    all_rels = IngredientToIngredient.objects.filter(child=ingredient_instance,
                                                                     parent_id=base.id)
                    all_rels[1].delete()

            else:
                ingredient_instance, _ = Ingredient.objects.get_or_create(
                    name=capwords(ingredient['ingredient']), owner=self.user)
        except Exception as e:
            print(f'Error: issue in save_and_add_ingredient, for {ingredient["ingredient"]}, base: {base_ingredient}, joined: {capwords(" ".join((specific_ingredient, base_ingredient)))}, {e}')

        ri = RecipeIngredient(
            ingredient=ingredient_instance,
            beverage=self.recipe,
        )
        ri.quantity = quantity or None
        ri.note = ingredient.get('note', None)
        ri.save()

    def save_and_add_garnish(self, update=False):
        # TODO: figure out why this triggers a duplicate integrity error

        if hasattr(self, 'garnish') and self.garnish:
            created = False
            self.garnish = self.garnish.lower().replace('garnish:', '').strip()
            try:
                # ingredient = Ingredient.objects.get(name=IngredientMapping.map(self.garnish.title()).title(), owner=self.user.id)
                ingredient = Ingredient.objects.get(name=capwords(self.garnish), owner=self.user.id)
            except Ingredient.DoesNotExist:
                ingredient = Ingredient.objects.create(name=capwords(self.garnish), owner_id=self.user.id, is_garnish=True)
                created = True

            if not created and not ingredient.is_garnish:
                ri = RecipeIngredient(
                    ingredient=ingredient,
                    beverage=self.recipe,
                    is_garnish=True,
                )
                ri.save()
            try:
                RecipeIngredient.objects.create(
                    ingredient=ingredient,
                    beverage=self.recipe,
                    is_garnish=True,
                    quantity=Quantity.objects.get_or_create(amount=1, divisor=None, unit=None)[0]
                )
            except Exception as e:
                print(f'Error: problem creating RecipeIngredient {ingredient}, {e}')
