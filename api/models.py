import csv
import re

from decimal import Decimal
from string import capwords
from unicodedata import numeric
from fractions import Fraction

from django.contrib.auth.models import User
from django.db import models


class MyFraction(Fraction):
    def __str__(self):
        if self.numerator < self.denominator:
            return f'{self.numerator}/{self.denominator}'
        else:
            return f'{self.numerator // self.denominator} {self.numerator % self.denominator}/{self.denominator}'


# class IngredientQuerySet(models.query.QuerySet):
#     def get_or_create(self, defaults=None, **kwargs):
#         if 'name' in kwargs:
#             kwargs['name'] = IngredientMapping.map(kwargs['name']).title()
#         return super(IngredientQuerySet, self).get_or_create(defaults=defaults, **kwargs)


# class IngredientManager(models.Manager):
#     def get_queryset(self):
#         return IngredientQuerySet(self.model)


class Ingredient(models.Model):
    name = models.CharField(max_length=1000)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    categories = models.ManyToManyField('self', blank=True, null=True, symmetrical=False,
                                        through='api.IngredientToIngredient')
    is_garnish = models.BooleanField(default=False)
    is_generic = models.BooleanField(default=False)

    # objects = IngredientManager()

    class Meta:
        unique_together = (('name', 'owner'),)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # if self.id is None:
        #     self.name = IngredientMapping.map(self.name)

        self.name = capwords(self.name)
        super().save(*args, **kwargs)


class IngredientToIngredient(models.Model):
    parent = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='child')
    child = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name='parent')


class Recipe(models.Model):
    COCKTAIL = 'COCKTAIL'
    SYRUP = 'SYRUP'
    CORDIAL = 'CORDIAL'
    BITTERS = 'BITTERS'
    OTHER = 'OTHER'

    TYPES = (
        (COCKTAIL, 'Cocktail'),
        (SYRUP, 'Syrup'),
        (CORDIAL, 'Cordial'),
        (BITTERS, 'Bitters'),
        (OTHER, 'Other')

    )
    name = models.CharField(max_length=1000)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    recipe_type = models.CharField(max_length=20, choices=TYPES, default=COCKTAIL)
    ingredients = models.ManyToManyField(Ingredient, through='api.RecipeIngredient')
    description = models.TextField(null=True)
    directions = models.TextField(null=True)
    attribution = models.TextField(null=True)
    source = models.CharField(null=True, blank=True, max_length=200)
    source_url = models.URLField(null=True, blank=True)
    glassware = models.CharField(max_length=100, null=True)
    tools = models.CharField(max_length=300, null=True)
    rating = models.FloatField(null=True, blank=True)
    non_alcoholic = models.BooleanField(default=False)
    notes = models.TextField(null=True, blank=True)
    date_added = models.DateTimeField(auto_now=True)
    date_modified = models.DateTimeField(auto_now=True)

    # TODO: when supporting multiple users this field may need to go on a user specific model
    # will probably want something equivalent to a user pantry (recipe book) to hold recipes
    shortlist = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Unit(models.Model):
    # TODO: is this how we want to handle units?
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=200, default=None, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = (('name', 'owner'),)

    def __str__(self):
        return self.name


class Quantity(models.Model):
    class Meta:
        verbose_name_plural = 'quantities'
        unique_together = [['amount', 'divisor', 'unit']]

    amount = models.DecimalField(decimal_places=2, max_digits=5)
    divisor = models.IntegerField(blank=True, null=True)
    unit = models.ForeignKey(Unit, null=True, blank=True, on_delete=models.CASCADE)

    @classmethod
    def create_quantity(cls, quantity, unit):
        if not quantity:
            return None
        if type(quantity) is int:
            result, _ = cls.objects.get_or_create(amount=quantity, divisor=None, unit=unit)
            return result
        if type(quantity) is float:
            quantity = Decimal(str(quantity))
            result, _ = cls.objects.get_or_create(amount=quantity, divisor=None, unit=unit)
            return result

        result, fr = None, None
        quantity = quantity.strip()
        dividend_divisor = quantity.split('/')
        # def is_multiple_fraction(q):
        #     if len(q.split()) == 2:
        #         first, second = q.split()
        #         if not first.isnumeric():
        #             return False
        #         else:
        #             fr = MyFraction(numerator= )
        #
        #     else:
        #         return False

        if len(quantity) < 3 and len(dividend_divisor[0].split()) == 1:
            try:
                fr = MyFraction(
                    str(numeric(quantity[0]) + numeric(quantity[1] if len(quantity) > 1 else '0')))
            except Exception as e:
                pass
        elif len(quantity) >= 3 and len(dividend_divisor[0].split()) > 1:
            first, second = dividend_divisor[0].split()
            dividend_divisor[0] = int(int(second) + int(first) * int(dividend_divisor[1]))
            dividend_divisor[1] = int(int(dividend_divisor[1]))
            try:
                fr = MyFraction(numerator=dividend_divisor[0], denominator=dividend_divisor[1])
            except Exception as e:
                pass
        try:
            int(quantity)
        except ValueError:
            pass
        else:
            fr = None

        if fr:
            result, _ = cls.objects.get_or_create(amount=fr.numerator,
                                                  divisor=fr.denominator,
                                                  unit=unit)
        elif len(dividend_divisor) == 1:
            try:
                result, _ = cls.objects.get_or_create(amount=dividend_divisor[0], divisor=None, unit=unit)
            except Exception as e:
                import pdb
                pdb.set_trace()

        else:
            result, _ = cls.objects.get_or_create(amount=dividend_divisor[0],
                                                  divisor=dividend_divisor[1],
                                                  unit=unit)
        return result

    def _is_integer(self, decimal):
        return decimal % 1 == 0

    def is_integer(self):
        return True if self._is_integer(self.amount) and not self.divisor else False

    def to_float(self):
        return float(self.amount/self.divisor) if self.divisor else float(self.amount)

    @property
    def display_amount(self):
        return str(int(self.amount)) if self._is_integer(self.amount) else str(self.amount)

    def display_int(self, num):
        return str(int(num)) if self._is_integer(num) else str(num)

    @property
    def display_fraction(self):
        dividend = self.amount
        integer = 0
        while dividend > self.divisor:
            dividend -= self.divisor
            integer += 1
        integer = f'{str(integer)} ' if integer else ''
        return f'{integer}{self.display_int(dividend)}/{str(self.divisor)}'

    def __str__(self):
        if self.amount and self.divisor:
            unit = f'{self.unit.name}' if getattr(self.unit, 'name', None) else ''
            return f'{self.display_fraction} {unit}'
        else:
            return str(f'{self.display_amount} {self.unit.name}'
                       if getattr(self.unit, 'name', None) else self.display_amount)


class RecipeIngredient(models.Model):
    class Meta:
        verbose_name_plural = 'recipe ingredients'

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    beverage = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    quantity = models.ForeignKey(Quantity, null=True, blank=True, on_delete=models.CASCADE)
    note = models.TextField(null=True)

    def __str__(self):
        if self.quantity:
            if (
                self.quantity.is_integer()
                and self.quantity.amount == 1
                and self.ingredient.name[0].isdigit()
            ):
                return self.ingredient.name
            return f'{self.quantity} {self.ingredient.name}'
        return self.ingredient.name


class Pantry(models.Model):
    owner = models.ForeignKey(User, null=False, on_delete=models.CASCADE)
    alert_when_out_of_stock = models.BooleanField(default=False)


class PantryIngredient(models.Model):
    class Meta:
        verbose_name_plural = 'pantry ingredients'

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    pantry = models.ForeignKey(Pantry, on_delete=models.CASCADE, related_name='pantry_ingredients')
    in_stock = models.BooleanField(default=True)

    def __str__(self):
        return f'{"✓" if self.in_stock else "✗"} {self.ingredient.name} - {self.id}'


class IngredientMapping(models.Model):
    '''
    Used to map from commonly seen processed ingredients to their base ingredient which should be
    stored as an actual ingredient.  One example would orange juice mapping to orange.
    '''

    original = models.CharField(max_length=200)
    final = models.CharField(max_length=200)
    plural = models.CharField(max_length=200)

    def __str__(self):
        return f'[{self.original} -> {self.final}]'

    @classmethod
    def parse_mappings_from_file(cls, file=None):
        if not file:
            file = 'ingredients_mapping.csv'
        mappings = []
        with open(file) as csvfile:
            mapping_reader = csv.reader(csvfile)
            for row in [row for row in mapping_reader][1:]:
                original, final, plural = row
                original = original.lower()
                final = final.lower()
                plural = plural.lower()
                if not cls.objects.filter(original=original.lower()):
                    mappings.append(cls(
                        original=original.strip(),
                        final=final.strip(),
                        plural=plural.strip()
                    ))
        cls.objects.bulk_create(mappings)


    @staticmethod
    def _automap(original):
        def get_matching_group(groups):
            for group in groups:
                if group:
                    return group
        translators = [
            re.compile(r'.*?(\w+) slices?|slices? of (\w+)'),
            re.compile(r'.*?(\w+) twist'),
            # lambda expr: any(current in expr.lower() for current in possible_matches),
        ]
        func_type = type(lambda x: x)
        for translator in translators:
            # if type(translator) is re.Pattern:
            #     if translator.match(original.lower()):
            #         return get_matching_group(translator.match(original.lower()).groups())
            # elif type(translator) is func_type:
            #     if translator(original):
            #         return
            if translator.match(original.lower()):
                print(f'in automap translator, matched: {get_matching_group(translator.match(original.lower()).groups())}')
                return get_matching_group(translator.match(original.lower()).groups())
        for final in IngredientMapping.objects.all().values_list('final', flat=True):
            if final in original:
                return final
        return None

    @classmethod
    def map(cls, ingredient):
        if cls.objects.count() == 0:
            cls.parse_mappings_from_file()

        found = cls.objects.filter(original=ingredient.lower())
        if found:
            return found[0].final
        else:
            automapped = cls._automap(ingredient)
            if automapped:
                return automapped
        return ingredient

    # TODO: use this class when importing from both plaintext and books
