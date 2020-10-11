import math
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

import nltk
from django.contrib.auth.models import User
from parsimonious.grammar import Grammar
from ingreedypy import Ingreedy as BaseIngreedy

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError

from api.models import Recipe, Ingredient, RecipeIngredient, PantryIngredient
from api.validators import RecipeValidator

custom_ingredient_grammar = Grammar(
        """
        ingredient_addition = multipart_quantity alternative_quantity? break? ingredient

        multipart_quantity
        = (quantity_fragment break?)*

        quantity_fragment
        = quantity
        / amount

        alternative_quantity
        = ~"[/]" break? multipart_quantity

        quantity
        = amount_with_conversion
        / amount_with_attached_units
        / amount_with_multiplier
        / amount_imprecise

        # 4lb (900g)
        amount_with_conversion
        = amount break? unit !letter break parenthesized_quantity

        # 1 kg
        amount_with_attached_units
        = amount break? unit !letter

        # two (five ounce)
        amount_with_multiplier
        = amount break? parenthesized_quantity

        # pinch
        amount_imprecise
        = imprecise_unit !letter

        parenthesized_quantity
        = open amount_with_attached_units close

        amount
        = float
        / mixed_number
        / fraction
        / integer
        / number

        break
        = " "
        / comma
        / hyphen
        / ~"[\t]"

        separator
        = break
        / "-"

        ingredient
        = (word (break word)* ~".*")

        open = "("
        close = ")"

        word
        = (letter+)

        float
        = (integer? ~"[.]" integer)

        mixed_number
        = (integer separator fraction)

        fraction
        = (multicharacter_fraction)
        / (unicode_fraction)

        multicharacter_fraction
        = (integer ~"[/]" integer)

        integer
        = ~"[0-9]+"

        letter
        = ~"[a-zA-Z]"

        comma
        = ","

        hyphen
        = "-"

        unit
        = english_unit
        / metric_unit
        / imprecise_unit

        english_unit
        = cup
        / fluid_ounce
        / gallon
        / ounce
        / pint
        / pound
        / quart
        / tablespoon
        / teaspoon
        / barspoon
        
        cup
        = "cups"
        / "cup"
        / "c."
        / "c"

        fluid_ounce
        = fluid break ounce

        fluid
        = "fluid"
        / "fl."
        / "fl"

        gallon
        = "gallons"
        / "gallon"
        / "gal."
        / "gal"

        ounce
        = "ounces"
        / "ounce"
        / "oz."
        / "oz"

        
        barspoon
        = "barspoons"
        / "barspoon"
        / "bar spoons"
        / "bar spoon"
    
        pint
        = "pints"
        / "pint"
        / "pt."
        / "pt"

        pound
        = "pounds"
        / "pound"
        / "lbs."
        / "lbs"
        / "lb."
        / "lb"

        quart
        = "quarts"
        / "quart"
        / "qts."
        / "qts"
        / "qt."
        / "qt"

        tablespoon
        = "tablespoons"
        / "tablespoon"
        / "tbsp."
        / "tbsp"
        / "tbs."
        / "tbs"
        / "T."
        / "T"

        teaspoon
        = "teaspoons"
        / "teaspoon"
        / "tsp."
        / "tsp"
        / "t."
        / "t"

        metric_unit
        = gram
        / kilogram
        / liter
        / milligram
        / milliliter

        gram
        = "grams"
        / "gram"
        / "gr."
        / "gr"
        / "g."
        / "g"

        kilogram
        = "kilograms"
        / "kilogram"
        / "kg."
        / "kg"

        liter
        = "liters"
        / "liter"
        / "l."
        / "l"

        milligram
        = "milligrams"
        / "milligram"
        / "mg."
        / "mg"

        milliliter
        = "milliliters"
        / "milliliter"
        / "ml."
        / "ml"

        imprecise_unit
        = dash
        / handful
        / pinch
        / touch

        dash
        = "dashes"
        / "dash"

        handful
        = "handfuls"
        / "handful"

        pinch
        = "pinches"
        / "pinch"

        touch
        = "touches"
        / "touch"

        number = written_number break

        written_number
        = "a"
        / "an"
        / "zero"
        / "one"
        / "two"
        / "three"
        / "four"
        / "five"
        / "six"
        / "seven"
        / "eight"
        / "nine"
        / "ten"
        / "eleven"
        / "twelve"
        / "thirteen"
        / "fourteen"
        / "fifteen"
        / "sixteen"
        / "seventeen"
        / "eighteen"
        / "nineteen"
        / "twenty"
        / "thirty"
        / "forty"
        / "fifty"
        / "sixty"
        / "seventy"
        / "eighty"
        / "ninety"

        unicode_fraction
        = ~"[¼]"u
        / ~"[½]"u
        / ~"[¾]"u
        / ~"[⅐]"u
        / ~"[⅑]"u
        / ~"[⅒]"u
        / ~"[⅓]"u
        / ~"[⅔]"u
        / ~"[⅕]"u
        / ~"[⅖]"u
        / ~"[⅗]"u
        / ~"[⅘]"u
        / ~"[⅙]"u
        / ~"[⅚]"u
        / ~"[⅛]"u
        / ~"[⅜]"u
        / ~"[⅝]"u
        / ~"[⅞]"u
        """)


class Ingreedy(BaseIngreedy):
    grammar = custom_ingredient_grammar

    def visit_fraction(self, node, visited_children):
        return visited_children[0]


def create_recipe(data, user):
    recipe_validator = RecipeValidator(**data)
    recipe_validator.with_user(user)
    recipe_validator.validate()
    recipe_validator.save()


def update_recipe(data, user):
    recipe_validator = RecipeValidator(**data)
    recipe_validator.with_user(user)
    recipe_validator.validate()
    recipe_validator.update()


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
        return counts, len(pos)

    def has_unit(text):
        return bool(Ingreedy().parse(text)['quantity'])

    if len(lines) > 1 and not has_unit(text):
        return True
    if has_unit(text) and len(lines) == 2:
        return False
    elif lines:
        line = lines[0]
        line, has_parens = remove_all_text_in_parens(line)
        tag_counts, length = tag_count_line(line)

        has_starting_number = line.split()[0].replace('.', '', 1).replace('/', '', 1).isdigit()
        # has_comma = ',' in tag_counts
        # has_sentence_delimiters = any(delimiter in tag_counts for delimiter in ('.', '?', '!'))
        # has_verb = any(vb in tag_counts for vb in ('VB', 'VBD', 'VBG', 'VBN', 'VBP', 'VBZ'))
        tags = set(tag_counts)
        difference = tags - POS_COMMONLY_FOUND_IN_INGREDIENTS
        has_two_or_more_non_ingredient_tags = len(difference) >= 2
        numerous_words_weight = max((length - 3), 0)*.5

        HAS_STARTING_NUMBER = -2
        HAS_UNIT = -2

        count = 0
        if has_starting_number:
            count += HAS_STARTING_NUMBER
        if has_unit(line):
            count += HAS_UNIT
        if has_two_or_more_non_ingredient_tags:
            count += len(difference)

        count += numerous_words_weight

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


def plaintext_garnish_handler(recipe, line):
    def add_to_garnish(text):
        print('line to replace: ', line)
        if recipe.garnish:
            recipe.garnish = recipe.garnish.strip() + ', ' + text
        else:
            recipe.garnish = text.strip()

    # TODO probably want to make into rule table
    if 'garnish:' in line.lower():
        add_to_garnish(line.lower().replace('garnish:', '').strip())
    elif '(as garnish)' in line.lower():
        add_to_garnish(line.lower().replace('(as garnish)', ''))
    elif '(wheel, as garnish)' in line.lower():
        add_to_garnish(line.lower().replace('(wheel, as garnish)', 'wheel'))
    elif 'garnish' in line.lower():
        add_to_garnish(line)
    else:
        return False
    return True


def _convert_to_fractional_text(number):
    if type(number) is int:
        return number
    fraction = Fraction(number).limit_denominator()

    numerator = fraction.numerator
    denominator = fraction.denominator

    # don't bother returning a text fraction if the granularity is too high
    if denominator > 10:
        return number

    if numerator > denominator:
        int_amount = math.floor(numerator / denominator)
        fraction_amount = numerator - (int_amount * denominator)
        return f'{int_amount} {str(Fraction(fraction_amount, denominator))}'
    else:
        return str(fraction)


def is_only_urls(lines):
    validator = URLValidator()
    for line in lines:
        try:
            validator(line)
        except ValidationError:
            return False
    return True


def is_url_then_recipe(lines):
    num_non_url = 0
    first = None
    validator = URLValidator()
    for line in lines:
        try:
            validator(line)
        except ValidationError:
            return first
        else:
            if not first:
                first = line
            else:
                return False
    return False


def clean_lines(lines):
    return [line for line in lines if line.strip()]

def convert_old_to_new_rating(rating):
    rating = Decimal(rating)
    if rating < Decimal('3'):
        return '1'
    elif rating < Decimal('3.8'):
        return '2'
    elif Decimal('3.8') <= rating < Decimal('4'):
        return '2.5'
    elif rating == Decimal('4'):
        return '3'
    elif Decimal('4') < rating < Decimal('4.4'):
        return '3.5'
    elif rating == Decimal('4.4'):
        return '3.5'
    elif rating == Decimal('4.5'):
        return '4'
    elif Decimal('4.5') < rating < Decimal('4.8'):
        return '4.5'
    elif Decimal('4.8') <= rating <= Decimal('5'):
        return '5'
    else:
        return rating


def create_recipe_from_plaintext(text):
    @dataclass
    class Recipe:
        title: str = None
        url_link: str = None
        rating: str = None
        ingredients: list = None
        directions: str = None
        description: str = None
        garnish: str = None
        reference: str = None
        source: str = None

    recipe = Recipe()
    text = text.replace('\t', ' ')
    lines = text.split('\n')
    title_line = lines[0]
    lines = clean_lines(lines)

    # parse out possible url
    if is_only_urls(lines):
        pass

    possible_url = is_url_then_recipe(lines)
    if not possible_url:
        possible_url = title_line.split()[-1]
        validator = URLValidator()

        try:
            validator(possible_url)
        except ValidationError:
            pass
        else:
            recipe.url_link = possible_url
            title_line = title_line.replace(possible_url, '').strip()
    else:
        lines.pop(0)
        title_line = lines[0]
    # parse out possible reference
    reference = get_text_within_parens(title_line)
    if reference:
        title_line, removed = remove_text_in_parens(title_line)
        title_line = title_line.strip()
        recipe.source = replace_reference_abbreviation_with_name(reference)

    # parse out possible rating
    if is_number(title_line.split()[0]):
       title_tokens = title_line.split()
       recipe.rating = title_tokens[0]
       recipe.rating = convert_old_to_new_rating(recipe.rating)
       recipe.title = ' '.join(title_tokens[1:])
    else:
        recipe.title = title_line

    recipe.ingredients = []

    lines = lines[1:]
    index = 0
    for index, line in enumerate(lines):
        if not line:
            continue
        if 'ingredients' == line.lower().strip() or 'ingredients:' == line.lower().strip():
            continue
        if 'directions' == line.lower().strip() or 'directions:' == line.lower().strip():
            continue
        if 'instructions' == line.lower().strip() or 'instructions:' == line.lower().strip():
            continue
        print('parsing possible ingredient', line)
        if recipe.ingredients and is_directions_classifier(line):
            break
        elif not recipe.ingredients and is_directions_classifier(line):
            # likely to be a description
            recipe.description = line
            continue

        if not plaintext_garnish_handler(recipe, line):
            print('to parse ingreedy: ', line)
            parsed_ingredient = Ingreedy().parse(line)
            try:
                parsed_ingredient['quantity'][0]['amount'] = \
                    _convert_to_fractional_text(parsed_ingredient['quantity'][0]['amount'])
            except:
                pass
            recipe.ingredients.append(parsed_ingredient)
        if recipe.garnish:
            print('done')
    directions = []
    for line in lines[index:]:
        if line.lower().startswith('garnish'):
            recipe.garnish = line
        else:
            directions.append(line)
    directions = '\n'.join(directions)

    recipe.directions = directions
    if (not recipe.garnish and any(text in recipe.directions.lower()
                                   for text in ['garnish:', 'garnish with'])):
        directions = recipe.directions
        directions = directions.lower()
        text_to_find = None
        if 'garnish:' in directions:
            text_to_find = 'garnish:'
        elif 'garnish with' in directions:
            text_to_find = 'garnish with'

        if text_to_find:
            recipe.garnish = directions[directions.find(text_to_find) + len(text_to_find):].strip()
    return recipe


def save_recipe_from_parsed_recipes(parsed):
    '''
        title: str = None
        url_link: str = None
        rating: str = None
        ingredients: list = None
        directions: str = None
        description: str = None
        garnish: str = None
        reference: str = None
        source: str = None
    '''

    def convert_ingredient(ingredient):
        return {
            'unit': ingredient['quantity'][0]['unit']
                if ingredient['quantity'] and ingredient['quantity'][0]['unit'] else None,
            'type': ingredient['quantity'][0]['unit_type']
                if ingredient['quantity'] and ingredient['quantity'][0]['unit_type'] else None,
            'amount': ingredient['quantity'][0]['amount']
                if ingredient['quantity'] and ingredient['quantity'][0]['amount'] else None,
            'ingredient': ingredient['ingredient']
        }

    recipe = {
        'name': parsed.title,
        'source_url': parsed.url_link,
        'source': parsed.reference,
        'garnish': parsed.garnish or '',
        'rating_set': 'rating_set',
        'rating': parsed.rating,
        'directions': parsed.directions,
        'description': parsed.description,
        'ingredients': [convert_ingredient(i) for i in parsed.ingredients],
        'recipe_type': Recipe.COCKTAIL,
    }
    if not parsed.rating:
        del recipe['rating']
    recipe_validator = RecipeValidator(**recipe)
    recipe_validator.with_user(User.objects.first())  # TODO: for now
    recipe_validator.validate()
    recipe_validator.save()
    return recipe_validator.recipe.id


def merge_ingredients_and_update_models(_id, name):
    # TODO: update to handle multiple users / auth
    existing = Ingredient.objects.get(name=name, owner=User.objects.first())

    ingredient_to_remove = Ingredient.objects.get(id=_id)
    recipe_ingredients_to_change = RecipeIngredient.objects.filter(ingredient=ingredient_to_remove)
    pantry_ingredients_to_change = PantryIngredient.objects.filter(ingredient=ingredient_to_remove)

    recipe_count = recipe_ingredients_to_change.update(ingredient=existing)
    pantry_count = pantry_ingredients_to_change.update(ingredient=existing)
    print(f'updated {recipe_count} recipe ingredients and {pantry_count} pantry ingredients')
    ingredient_to_remove.delete()
