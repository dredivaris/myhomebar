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


class Beverage(models.Model):
    name = models.CharField(max_length=1000)
    owner = models.ForeignKey(User)
    ingredients = models.ManyToManyField(Ingredient, through='BeverageIngredients')
    description = models.TextField(null=True)
    directions = models.TextField(null=True)

    def __str__(self):
        return self.name


class Unit(models.Model):
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


class BeverageIngredients(models.Model):
    class Meta:
        verbose_name_plural = 'beverage ingredients'

    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    beverage = models.ForeignKey(Beverage, on_delete=models.CASCADE)
    quantity = models.ForeignKey(Quantity, on_delete=models.CASCADE)

    def __str__(self):
        return '{} {} of {}'.format(
            self.quantity.amount, self.quantity.unit.name, self.ingredient.name)