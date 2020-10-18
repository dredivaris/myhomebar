from ingreedypy import Ingreedy as BaseIngreedy
from parsimonious import Grammar

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
        / rinse
        / dr
        / twst
        / t

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
        
        rinse
        = "rinses"
        / "rinse"
        
        dr
        = "drs"
        / "dr"
        
        twst
        = "twsts"
        / "twst"
        
        t
        = "ts"
        / "t"

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

replacement_mapper = {
    '⁄': '/'
}


class Ingreedy(BaseIngreedy):
    grammar = custom_ingredient_grammar

    def visit_fraction(self, node, visited_children):
        return visited_children[0]