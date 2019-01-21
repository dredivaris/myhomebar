from django.contrib.auth.models import User
from django.db import models


class Ingredient(models.Model):
    name = models.CharField(max_length=1000)


class Beverage(models.Model):
    name = models.CharField(max_length=1000)
    owner = models.ForeignKey(User)
    ingredients = models.ManyToManyField(Ingredient, through='BeverageIngredients')


class Unit(models.Model):
    name = models.CharField(max_length=200)


class Quantity(models.Model):
    amount = models.DecimalField(decimal_places=2, max_digits=3)
    divisor = models.IntegerField(blank=True)
    unit = models.ForeignKey(Unit)


class BeverageIngredients(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    beverage = models.ForeignKey(Beverage, on_delete=models.CASCADE)
    quantity = models.ForeignKey(Quantity, on_delete=models.CASCADE)
