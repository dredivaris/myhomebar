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


class Ingredient(models.Model):
    name = models.CharField(max_length=1000)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)
    is_garnish = models.BooleanField(default=False)

    class Meta:
        unique_together = (('name', 'owner'),)

    @property
    def is_generic(self):
        return True if not self.parent else False

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.title()
        super().save(*args, **kwargs)


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
    notes = models.TextField(null=True, blank=True)

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
        result, fr = None, None
        dividend_divisor = quantity.split('/')
        if len(quantity) < 3:
            try:
                fr = MyFraction(
                    str(numeric(quantity[0]) + numeric(quantity[1] if len(quantity) > 1 else '0')))
            except Exception as e:
                import pdb
                pdb.set_trace()

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
            except:
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

    def __str__(self):
        if self.quantity:
            if self.quantity.is_integer() and self.quantity.amount == 1:
                if self.ingredient.name[0].isdigit():
                    return self.ingredient.name
            return f'{self.quantity} {self.ingredient.name}'
        return self.ingredient.name