import re
import unicodedata
import nltk

from collections import namedtuple
from enum import Enum


class Step(Enum):
    NAME = 1
    ATTRIBUTION = 2
    INGREDIENTS = 3
    GARNISH = 4
    DIRECTIONS = 5
    GLASSWARE = 6
    DESCRIPTION = 7
    TOOLS = 8

UNITS = {
    'ml', 'oz', 'ounce', 'ounces', 'millileter', 'millileters', 'milliliter', 'milliliters',
    'dash', 'dashes', 'teaspoon', 'teaspoons', 'gram', 'grams'
}
ALL_UNITS = list(UNITS) + [u.upper() for u in UNITS]

GLASSWARE = {
    'coupe', 'old-fashioned glass', 'old fashioned glass', 'double old-fashioned glass',
    'rocks glass', 'double rocks glass', 'fizz glass', 'snifter', 'pewter cup', 'mug',
    'highball glass', 'nick and nora glass'
}


StepReq = namedtuple('StepReq', 'step, required')

def string_found(string1, string2):
    return re.search(r'\b%s\b' % (re.escape(string1)), string2) is not None

class InvalidParseStepException(Exception):
    pass

class SkipToNextException(Exception):
    pass

class RecipeFormat:
    recipe_formats = {
        'DEATH_CO': {
            'to_split_sentence_directions': True,
            'steps': [
                Step.NAME,
                Step.ATTRIBUTION,
                Step.DESCRIPTION,
                Step.INGREDIENTS,
                Step.GARNISH,
                Step.DIRECTIONS],
            'optional': [Step.GARNISH, Step.DESCRIPTION]
        },
        'PDT': {
            'to_split_sentence_directions': False,
            'steps': [
                Step.NAME,
                Step.DESCRIPTION,
                Step.INGREDIENTS,
                Step.DIRECTIONS,
                Step.GARNISH,
                Step.ATTRIBUTION],
            'optional': []
        },
        'DEAD_RABBIT_MIXOLOGY_MAYHEM': {
            'to_split_sentence_directions': False,
            'steps': [
                Step.NAME,
                Step.INGREDIENTS,
                Step.DIRECTIONS,
                Step.GLASSWARE,
                Step.GARNISH,
                Step.ATTRIBUTION],
            'optional': []
        },
        'COCKTAIL_CODEX': {
            'to_split_sentence_directions': False,
            'steps': [
                Step.NAME,
                Step.ATTRIBUTION,
                Step.DESCRIPTION,
                Step.INGREDIENTS,
                Step.GARNISH,
                Step.DIRECTIONS],
            'optional': []
        }
    }


class IndividualRecipeParser(object):
    number_matcher = re.compile(r"(^[\xbc\xbd\xbe])|(^(\d*[.,/]?\d*))")
    ingredient_parser = re.compile(
        r"^(((\d*[.,/]?\d*)?[\xbc\xbd\xbe])|(\d*[.,/]?\d*)) ?({})?[\. ](.*)".format('|'.join(ALL_UNITS)))
    juice_of_parser = re.compile(r"^Juice of (\d+) (\w+)(?:.*)")
    alternative_unit_location_parser = re.compile(r"^.*(?:(\d+) ?({}))".format('|'.join(ALL_UNITS)))
    # g 1 is number, g 4 is unit, g 5 is ingredient

    def __init__(self):
        self.formats = {}
        for format in RecipeFormat.recipe_formats.keys():
            self.formats[format] = None

    def __call__(self, recipe_text, format_type=None):
        for format in RecipeFormat.recipe_formats.keys():
            self.formats[format] = None

        if format_type:
            self.formats[format_type] = self.parse_with_format(format_type, recipe_text)
        else:
            for format in RecipeFormat.recipe_formats.keys():
                try:
                    self.formats[format] = self.validate_parsed_recipe(
                        self.parse_with_format(format, recipe_text))
                except InvalidParseStepException as e:
                    pass
        return self.formats

    def is_ingredient(self, text):
        num_match = self.number_matcher.match(text)
        print('checking is ingredient', num_match, num_match.group(0), text)
        if not num_match:
            return False
        if not num_match.group(0):
            return False

        # if not any(string_found(unit, text) for unit in UNITS):
        #     return False

        return True

    def is_basic_text(self, text):
        if self.is_ingredient(text):
            return False
        return True

    def is_garnish(self, text):
        return True if 'garnish' in text.lower() else False

    def is_name(self, text):
        return self.is_basic_text(text)

    def is_attribution(self, text):
        return self.is_basic_text(text)

    def is_directions(self, text):
        if self.is_ingredient(text):
            return False

        return True

    def is_glassware(self, text):
        if 'glass' in text.lower():
            return True
        return False

    def is_description(self, text):
        return self.is_basic_text(text)

    def is_tools(self, text):
        pass

    def has_named_entity(self, text):
        pass

    def validate_parsed_recipe(self, parsed):
        if not parsed['ingredients']:
            return None
        if not parsed['name']:
            return None
        if not parsed['directions']:
            return None
        return parsed

    def parse_with_format(self, format_key, recipe_text):
        format = RecipeFormat.recipe_formats[format_key]
        lines = recipe_text.splitlines()

        tools_parsed, garnish_parsed, glass_parsed = False, False, False
        specific_parse_mapping = {Step.TOOLS: False, Step.GARNISH: False, Step.GLASSWARE: False}

        parsed_recipe = {
            'ingredients': [],
            'directions': ''
        }
        steps = format['steps']
        current_step_increment = 0

        def parse_name(text):
            print('in name')

            if not self.is_name(text):
                raise InvalidParseStepException(text)
            parsed_recipe['name'] = text.strip()

        def parse_attribution(text):
            print('in attribution')

            if not self.is_attribution(text):
                raise InvalidParseStepException()
            parsed_recipe['attribution'] = text.strip()

        def parse_ingredient(text):
            print('in ingredient', text)
            if text.lower().startswith('garnish'):
                print('ingredient is a garnish')
                parsed_recipe['garnish'] = text.strip()
            else:
                cleaned_text = text.strip()
                match = self.ingredient_parser.match(cleaned_text)
                if not match:
                    match = self.juice_of_parser.match(cleaned_text)
                    if not match:
                        print('ingredient ', text, ' does not match!')
                        raise SkipToNextException()
                    ingredient = {
                        'amount': match.group(1),
                        'ingredient': match.group(2) + ' juice',
                    }
                    match = self.alternative_unit_location_parser.match(cleaned_text)
                    if match:
                        ingredient['amount'] = match.group(1)
                        ingredient['unit'] = match.group(2)
                else:
                    ingredient = {
                        'amount': match.group(1),
                        'unit': match.group(5),
                        'ingredient': match.group(6).strip(),
                    }
                parsed_recipe['ingredients'].append(ingredient)

        def parse_directions(text):
            nonlocal current_step_increment
            print('in parse directions', text)
            if not self.is_basic_text(text):
                print('its not basic text')
                raise InvalidParseStepException()
            if format['to_split_sentence_directions']:
                print('in to split sentence')
                tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
                lines = tokenizer.tokenize(text)
                parsed_recipe['directions'] = ''
                for line in lines:
                    print('checking split line ', line)
                    if self.is_glassware(line):
                        parse_glassware(line)
                    if 'garnish' not in parsed_recipe and self.is_garnish(line):
                        parse_garnish(line)
                    parsed_recipe['directions'] += line.strip() + ' '
            else:
                print('in individual direction check')
                if 'garnish' not in parsed_recipe and self.is_garnish(text):
                    print('parsing garnish early')
                    parse_garnish(text)
                    if parsed_recipe['directions']:
                        current_step_increment += 1
                parsed_recipe['directions'] += text.strip() + ' '
            parsed_recipe['directions'] = parsed_recipe['directions'].strip()
            # todo: add sentence delimeters if they do not exist

        def parse_description(text):
            print('in description')

            if not self.is_basic_text(text):
                raise InvalidParseStepException()
            parsed_recipe['description'] = text.strip()

        def parse_garnish(text):
            print('in garnish parser', text)

            if 'garnish' in parsed_recipe and parsed_recipe['garnish']:
                raise SkipToNextException()
            print('garnish 1', parsed_recipe)
            if not text.lower().startswith('garnish') and format['to_split_sentence_directions'] \
                    and self.is_garnish(text) and not parsed_recipe['directions']:
                print('oh no', self.is_garnish(text), parsed_recipe['directions'])
                raise SkipToNextException()

            if not self.is_garnish(text):
                print('its not really a garnish?')
                raise InvalidParseStepException()
            print('garnish 2')
            parsed_recipe['garnish'] = text.strip()

        def parse_glassware(text):
            print('in glassware')
            if not self.is_glassware(text):
                raise InvalidParseStepException()
            for glass in GLASSWARE:
                if glass in text.lower():
                    parsed_recipe['glassware'] = glass

        def get_step():
            nonlocal current_step_increment

            step = steps[current_step_increment]
            for specific_parse_type, is_done in specific_parse_mapping.items():
                if step == specific_parse_type and is_done:
                    current_step_increment += 1
                    step = steps[current_step_increment]
            return step

        def parse_tagged_lines(current_line):
            TOOL_TEXT, GARNISH_TEXT, GLASS_TEXT = 'tools:', 'garnish:', 'glass:'
            if current_line.lower().startswith(TOOL_TEXT):
                current_line = current_line[len(TOOL_TEXT):].strip()
                parsed_recipe['tools'] = current_line
                specific_parse_mapping[Step.TOOLS] = True
            elif current_line.lower().startswith(GARNISH_TEXT):
                current_line = current_line[len(GARNISH_TEXT):].strip()
                parsed_recipe['garnish'] = current_line
                specific_parse_mapping[Step.GARNISH] = True
            elif current_line.lower().startswith(GLASS_TEXT):
                current_line = current_line[len(GLASS_TEXT):].strip()
                parsed_recipe['glassware'] = current_line
                specific_parse_mapping[Step.GLASSWARE] = True
            else:
                return False

            return True

        choose_parser_for = {
            Step.NAME: parse_name,
            Step.ATTRIBUTION: parse_attribution,
            Step.INGREDIENTS: parse_ingredient,
            Step.GARNISH: parse_garnish,
            Step.DIRECTIONS: parse_directions,
            Step.GLASSWARE: parse_glassware,
            Step.DESCRIPTION: parse_description,
        }

        for line in lines:
            if not line:
                continue
            current_step = get_step()
            try:
                if parse_tagged_lines(line):
                    continue
                if current_step == Step.INGREDIENTS or \
                        (current_step == Step.DIRECTIONS and
                         not format['to_split_sentence_directions']):
                    try:
                        choose_parser_for[current_step](line)
                    except InvalidParseStepException:
                        current_step_increment += 1
                        choose_parser_for[get_step()](line)

                else:
                    choose_parser_for[current_step](line)
                    current_step_increment += 1
            except InvalidParseStepException as e:
                print('in exception, about to check for optional', e, current_step,
                      format['optional'], line)
                if current_step in format['optional']:
                    print('failed step was actually optional')
                    current_step_increment += 1
                    choose_parser_for[get_step()](line)
                else:
                    print('current step is', current_step, format['optional'], line)

                    raise InvalidParseStepException(e)
            except SkipToNextException:
                try:
                    current_step_increment += 1
                    choose_parser_for[get_step()](line)
                except SkipToNextException:
                    current_step_increment += 1
                    choose_parser_for[get_step()](line)
        return parsed_recipe

    # TODO: next: add known parts, were if we know something is say, a garnish, we proces and remove it from the list
    # for example, Tools: Glass: and Garnish: here: http://imbibemagazine.com/garibaldi-cocktail/

# def find_named_entities(text):
#     import nltk
#     tokens = nltk.word_tokenize(text)
#     tagged = nltk.pos_tag(tokens)
#     entities = nltk.chunk.ne_chunk(tagged)
#     results = []
#     for subtree in entities.subtrees():
#          if subtree.label() == 'PERSON':
#               results += list(subtree.leaves())
#     return results
