from django.contrib.auth.models import User
from django.db import models


class Ingredient(models.Model):
    name = models.CharField(max_length=1000)
    parent = models.ForeignKey('self', blank=True, null=True)
    is_garnish = models.BooleanField(default=False)

    @property
    def is_generic(self):
        return True if not self.parent else False

    def __str__(self):
        return self.name


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
    owner = models.ForeignKey(User)
    recipe_type = models.CharField(max_length=20, choices=TYPES, default=COCKTAIL)
    ingredients = models.ManyToManyField(Ingredient, through='RecipeIngredients')
    description = models.TextField(null=True)
    directions = models.TextField(null=True)
    attribution = models.TextField(null=True)
    glassware = models.CharField(max_length=100, null=True)
    tools = models.CharField(max_length=300, null=True)
    rating = models.FloatField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name


class Unit(models.Model):
    # TODO: is this how we want to handle units?
    name = models.CharField(max_length=200)

    def __str__(self):
        return self.name


class Quantity(models.Model):
    class Meta:
        verbose_name_plural = 'quantities'

    amount = models.DecimalField(decimal_places=2, max_digits=3)
    divisor = models.IntegerField(blank=True, null=True)
    unit = models.ForeignKey(Unit, null=True, blank=True)

    def __str__(self):
        return '{} {}'.format(self.amount, self.unit.name) if self.unit.name else self.amount


class RecipeIngredients(models.Model):
    class Meta:
        verbose_name_plural = 'recipe ingredients'

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    beverage = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    quantity = models.ForeignKey(Quantity, on_delete=models.CASCADE)

    def __str__(self):
        return '{} {} of {}'.format(
            self.quantity.amount, self.quantity.unit.name, self.ingredient.name)