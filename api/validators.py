from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from graphql import GraphQLError

from api.individual_recipe_parser import INGREDIENT_PARSER, JUICE_OF_PARSER, \
    ALTERNATIVE_UNIT_LOCATION_PARSER
from api.models import Recipe, Ingredient, Unit, Quantity, RecipeIngredient


class RecipeValidator(object):
    def __init__(self, **kwargs):
        self.recipe_raw = kwargs
        self.recipe = None

    def validate(self):
        self.ingredients = self.process_ingredients()
        self.recipe_type = self.process_type()
        self.process_garnish()
        self.process_rating()

    def save(self):
        print('print 1')
        self.recipe_raw['name'] = self.recipe_raw['name'].title()
        self.recipe = Recipe(**self.recipe_raw)
        print('print 2')

        # todo: remove this and use a real owner:
        self.recipe.owner = User.objects.get(username='root')
        self.recipe.save()
        print('print 3')
        for ingredient in self.ingredients:
            self.save_and_add_ingredient(ingredient)
            print('print 4')

        self.save_and_add_garnish()
        print('print 5')

    def process_ingredients(self):
        ingredient_text = self.recipe_raw['ingredients']
        ingredients = []
        ingredients_raw = ingredient_text.splitlines()

        for raw_ingredient in ingredients_raw:
            cleaned_text = raw_ingredient.strip()

            match = INGREDIENT_PARSER.match(cleaned_text)
            if not match:
                match = JUICE_OF_PARSER.match(cleaned_text)
                if not match:
                    raise ValidationError('Could not match ingredient')
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
                    'unit': match.group(5),
                    'ingredient': match.group(6).strip(),
                }
            ingredients.append(ingredient)

        self.recipe_raw.pop('ingredients')
        return ingredients

    def process_type(self):
        recipe_type = self.recipe_raw['recipe_type']
        if recipe_type not in {recipe_type[0] for recipe_type in Recipe.TYPES}:
            raise GraphQLError('Invalid recipe type.')
        self.recipe_raw.pop('recipe_type')
        return recipe_type

    def process_garnish(self):
        # todo: we want to support multiple garnishes in the future and garnish units
        garnish = self.recipe_raw['garnish'].strip()
        if garnish:
            self.garnish = garnish
        self.recipe_raw.pop('garnish')

    def process_rating(self):
        if not self.recipe_raw['rating_set']:
            self.recipe_raw.pop('rating')
        self.recipe_raw.pop('rating_set')

    def save_and_add_ingredient(self, ingredient):
        # todo: change owner to current owner
        unit, _ = Unit.objects.get_or_create(name=ingredient['unit'].lower(),
                                             owner=User.objects.get(username='root'))
        print('print 6')

        quantity = Quantity.create_quantity(ingredient['amount'], unit=unit)
        print('print 7')

        ingredient, _ = Ingredient.objects.get_or_create(
            name=ingredient['ingredient'].title(), owner=User.objects.get(username='root'))
        print('print 8')
        RecipeIngredient.objects.create(
            ingredient=ingredient,
            beverage=self.recipe,
            quantity=quantity
        )

    def save_and_add_garnish(self):
        if hasattr(self, 'garnish') and self.garnish:
            ingredient, created = Ingredient.objects.get_or_create(
                name=self.garnish.title(),
                owner=User.objects.get(username='root'),
                defaults={'is_garnish': True})
            if not created and not ingredient.is_garnish:
                raise GraphQLError('Garnish already exists as non-garnish ingredient')
            RecipeIngredient.objects.create(
                ingredient=ingredient,
                beverage=self.recipe,
                quantity=Quantity.objects.get_or_create(amount=1, unit=None)[0]
            )
