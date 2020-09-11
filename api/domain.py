import re
from collections import Counter
from dataclasses import dataclass

import nltk
from ingreedypy import Ingreedy

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from api.validators import RecipeValidator


def create_recipe(data, user):
    recipe_validator = RecipeValidator(**data)
    recipe_validator.with_user(user)
    recipe_validator.validate()
    recipe_validator.save()


def parse_plaintext_recipe(plaintext_recipe):
    pass


def tokenize_recipes_from_plaintext(text):
    lines = text.split('\n')
    recipe_texts = []
    current_lines = []
    blank_lines = 0
    for line in lines:
        line = line.strip()
        if not line:
            blank_lines += 1

        if not current_lines:
            if line:
                current_lines.append(line)
                blank_lines = 0
        elif blank_lines > 1:
            recipe_texts.append('\n'.join(current_lines))
            current_lines = []
        else:
            if line:
                current_lines.append(line)
    if current_lines:
        recipe_texts.append('\n'.join(current_lines))

    return [
        create_recipe_from_plaintext(plaintext_recipe)
        for plaintext_recipe in recipe_texts
    ]


def clean(text):
    return text.replace('\xa0', '')

def remove_text_in_parens(text):
    start = text.find('(')
    end = text.find(')')
    if start != -1 and end != -1:
        result = text[:start-1] + text[end+1:]
        return result, True
    return text, False

def remove_all_text_in_parens(text):
    text, result = remove_text_in_parens(text)
    while result is True:
        text, result = remove_text_in_parens(text)
    return text, result


def is_directions_classifier(text):
    text = clean(text)
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    lines = tokenizer.tokenize(text)

    POS_COMMONLY_FOUND_IN_INGREDIENTS = {'(', ')', ',', 'CC', 'CD', 'IN', 'JJ', 'NN', 'NNP', 'NNS', 'RB', 'VB', 'VBD', 'VBN', 'VBZ', '.'}

    def tag_count_line(line_text):
        pos = nltk.pos_tag(nltk.word_tokenize(line_text))
        counts = Counter(i[1] for i in pos)
        return counts


    def has_unit(text):
        return bool(Ingreedy().parse(text)['quantity'])

    if len(lines) > 1 and not has_unit(text):
        return True
    else:
        line = lines[0]
        line, has_parens = remove_all_text_in_parens(line)
        tag_counts = tag_count_line(line)

        has_starting_number = line.split()[0].replace('.', '', 1).replace('/', '', 1).isdigit()
        # has_comma = ',' in tag_counts
        # has_sentence_delimiters = any(delimiter in tag_counts for delimiter in ('.', '?', '!'))
        # has_verb = any(vb in tag_counts for vb in ('VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'))
        tags = set(tag_counts)
        difference = tags - POS_COMMONLY_FOUND_IN_INGREDIENTS
        has_two_or_more_non_ingredient_tags = len(difference) >= 2

        HAS_STARTING_NUMBER = -2
        HAS_UNIT = -2

        count = 0
        if has_starting_number:
            count += HAS_STARTING_NUMBER
        if has_unit(line):
            count += HAS_UNIT
        if has_two_or_more_non_ingredient_tags:
            count += len(difference)

        if count > 0:
            return True, count
        else:
            return False

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def get_text_within_parens(text):
    start = text.find('(')
    end = text.find(')')

    if start != -1 and end != -1:
        return text[start + 1:end]
    return None

def replace_reference_abbreviation_with_name(reference):
    reference_mapping = {
        'amaro': 'Amaro: The Spirited World of Bittersweet, Herbal Liqueurs, with Cocktails, Recipes, and Formulas',
        'drdm': 'The Dead Rabbit Drinks Manual: Secret Recipes and Barroom Tales from Two Belfast Boys Who Conquered the Cocktail World',
        'imbibe': 'Imbibe! Updated and Revised Edition: From Absinthe Cocktail to Whiskey Smash, a Salute in Stories and Drinks to "Professor" Jerry Thomas, Pioneer of the American Bar',
        'imbibe!': 'Imbibe! Updated and Revised Edition: From Absinthe Cocktail to Whiskey Smash, a Salute in Stories and Drinks to "Professor" Jerry Thomas, Pioneer of the American Bar',
        'd&c': 'Death & Co: Modern Classic Cocktails',
        'death & co': 'Death & Co: Modern Classic Cocktails',
        'bittermans': "Bitterman's Field Guide to Bitters & Amari: 500 Bitters; 50 Amari; 123 Recipes for Cocktails, Food & Homemade Bitters (Volume 2)",
        'a proper drink': 'A Proper Drink: The Untold Story of How a Band of Bartenders Saved the Civilized Drinking World',
        'proper drink': 'A Proper Drink: The Untold Story of How a Band of Bartenders Saved the Civilized Drinking World',
        'sasha': 'Regarding Cocktails',
        'regarding cocktails': 'Regarding Cocktails',
        'pdt': "The PDT Cocktail Book: The Complete Bartender's Guide from the Celebrated Speakeasy",
        'vermouth book': "Vermouth: The Revival of the Spirit that Created America's Cocktail Culture (First Edition)",
        'vermouth': "Vermouth: The Revival of the Spirit that Created America's Cocktail Culture (First Edition)",
        'smugglers cove': "Smuggler's Cove: Exotic Cocktails, Rum, and the Cult of Tiki",
        'smugglers': "Smuggler's Cove: Exotic Cocktails, Rum, and the Cult of Tiki",
        'sc': "Smuggler's Cove: Exotic Cocktails, Rum, and the Cult of Tiki",
        'meehans': "Meehan's Bartender Manual",
        'the craft cocktail party': 'The Craft Cocktail Party: Delicious Drinks for Every Occasion',
        'codex': 'Cocktail Codex: Fundamentals, Formulas, Evolutions',
        'heritage': 'South: Essential Recipes and New Explorations',
        'beta': 'Beta Cocktails.',
        'beach bum berry remixed': 'Beach Bum Berry Remixed',
        'bbb': 'Beach Bum Berry Remixed',
        'beach bum berry': 'Beach Bum Berry Remixed',
        'nightcap': 'Nightcap: More than 40 Cocktails to Close Out Any Evening (Cocktails Book, Book of Mixed Drinks, Holiday, Housewarming, and Wedding Shower Gift)',
        'dll': "Drinking Like Ladies: 75 modern cocktails from the world's leading female bartenders; Includes toasts to extraordinary women in history",
        'drinks': '',
        'ijhftd': "I'm Just Here for the Drinks: A Guide to Spirits, Drinking and More Than 100 Extraordinary Cocktails",
        'drinking like ladies': "Drinking Like Ladies: 75 modern cocktails from the world's leading female bartenders; Includes toasts to extraordinary women in history",
        'contraband': "Contraband Cocktails: How America Drank When It Wasn't Supposed To",
        'canon': 'The Canon Cocktail Book: Recipes from the Award-Winning Bar',
        'nomad': 'The NoMad Cocktail Book',
        'fernet book': "Bartender's Handshake: The Cult of Fernet-Branca, with Cocktail Recipes and Lore",
    }
    try:
        return reference_mapping[reference]
    except KeyError:
        return None

def create_recipe_from_plaintext(text):
    @dataclass
    class Recipe:
        title: str = None
        url_link: str = None
        rating: str = None
        ingredients: list = None
        garnish: str = None
        reference: str = None

    recipe = Recipe()
    lines = text.split('\n')
    title_line = lines[0]

    # parse out possible url
    possible_url = title_line.split()[-1]
    validator = URLValidator()

    try:
        validator(possible_url)
    except ValidationError:
        pass
    else:
        recipe.url_link = possible_url
        title_line = title_line.replace(possible_url, '').strip()

    # parse out possible reference
    reference = get_text_within_parens(title_line)
    if reference:
        title_line, removed = remove_text_in_parens(title_line)
        title_line = title_line.strip()
        recipe.reference = replace_reference_abbreviation_with_name(reference)

    # parse out possible rating
    if is_number(title_line.split()[0]):
       title_tokens = title_line.split()
       recipe.rating = title_tokens[0]
       recipe.title = ' '.join(title_tokens[1:])
    else:
        recipe.title = title_line

    recipe.ingredients = []

    lines = lines[1:]
    index = 0
    for index, line in enumerate(lines):
        if 'ingredients' == line.lower().strip() or 'ingredients:' == line.lower().strip():
            continue
        if 'directions' == line.lower().strip() or 'directions:' == line.lower().strip():
            continue
        if 'instructions' == line.lower().strip() or 'instructions:' == line.lower().strip():
            continue

        if recipe.ingredients and is_directions_classifier(line):
            break

        if 'garnish:' in line.lower():
            recipe.garnish = line.lower().replace('garnish:', '').strip()
        elif 'garnish' in line.lower():
            recipe.garnish = line
        else:
            parsed_ingredient = Ingreedy().parse(line)
            recipe.ingredients.append(parsed_ingredient)

    directions = '\n'.join(lines[index:])
    recipe.directions = directions
    return recipe
