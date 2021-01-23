import os

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

import yaml

from api.domain import plaintext_garnish_handler, _convert_to_fractional_text, convert_ingredient
from api.models import Recipe

from django.core.validators import URLValidator
from api.general.core import Ingreedy
from api.validators import RecipeValidator


def parse_yaml_file(filepath):
    with open(filepath) as file:
        all_text = file.read()
        print(f'currently set to parse: {all_text}')
        return parse_yaml(all_text)


def parse_yaml(yaml_text):
    return yaml.load(yaml_text)


def fix_spaced_fraction(ingredient):
    if not ingredient:
        return ingredient
    vals = ingredient.strip().split()
    val1, val2 = vals[0], vals[1]
    if (val1.replace('/', '').isnumeric() and val2.replace('/', '').isnumeric()
            and not val1.isnumeric() or not val2.isnumeric()):
        val_start = ''.join((val1, val2))
        return ' '.join([val_start] + vals[2:])
    return ingredient


def create_recipe_from_yaml(yaml_dict, default_source):
    name = yaml_dict['name']
    raw_source = yaml_dict['source'] or default_source

    validator = URLValidator()
    source_url, source = None, None
    try:
        validator(raw_source)
    except ValidationError:
        source = raw_source
    else:
        source_url = raw_source

    existing = Recipe.objects.filter(name=name.strip(), source=raw_source.strip(),
                                     source_url=source_url)
    if existing:
        return None

    # recipe = Recipe.objects.create(
    #     name=name,
    #     source=raw_source,
    #     directions=yaml_dict['directions'],
    #     description=yaml_dict['notes'],
    # )

    # TODO: add connection to create actual recipe
    recipe = {
        'name': name,
        'source_url': source_url,
        'source': source,
        'garnish': None,
        # 'rating': parsed.rating,
        'directions': yaml_dict['directions'],
        'description': yaml_dict.get('notes', None),
        'recipe_type': Recipe.COCKTAIL,
    }


    """
    if not parsed.rating:
        del recipe['rating']
    recipe_validator = RecipeValidator(**recipe)
    recipe_validator.with_user(User.objects.first())  # TODO: for now
    recipe_validator.validate()
    recipe_validator.save()
    return recipe_validator.recipe.id

    """


    # recipe = Recipe(
    #     name=name,
    #     source=raw_source,
    #     directions=yaml_dict['directions'],
    #     description=yaml_dict['notes'],
    # )

    # parse ingredients
    ingredients = [line.strip() for line in yaml_dict['ingredients'].split('\n') if line.strip()]
    # print(ingredients)

    parsed_ingredients = []
    for ingredient in ingredients:
        parsed_ingredient = None
        if not plaintext_garnish_handler(recipe, ingredient):
            print(ingredient)
            ingredient = fix_spaced_fraction(ingredient)
            parsed_ingredient = Ingreedy().parse(ingredient)
            try:
                parsed_ingredient['quantity'][0]['amount'] = \
                    _convert_to_fractional_text(parsed_ingredient['quantity'][0]['amount'])
            except:
                pass
            parsed_ingredients.append(parsed_ingredient)
            print(f'parsed ingredient is {parsed_ingredient}')

    recipe['ingredients'] = [convert_ingredient(i, recipe) for i in parsed_ingredients]

    if recipe['garnish']:
        print(f'garnish: {recipe["garnish"]}')

    recipe_validator = RecipeValidator(**recipe)
    recipe_validator.with_user(User.objects.first())  # TODO: for now
    recipe_validator.validate()
    recipe_validator.save()


def import_all_yaml_files_in_yaml_dir(directory, default_source):
    for filename in os.listdir(directory):
        if filename.endswith('.yml'):
            if not directory.endswith('/'):
                directory += '/'
            parsed = parse_yaml_file(directory + filename)
            # print(directory+filename)
            # print(parsed)
            create_recipe_from_yaml(parsed, default_source)
