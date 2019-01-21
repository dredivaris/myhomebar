from django.contrib.auth.models import User
from django.db import models


class Ingredient(models.Model):
    name = models.CharField()


class Beverage(models.Model):
    name = models.CharField()
    owner = models.ForeignKey(User)
    ingredients = models.ManyToManyField(Ingredient, through='BeverageIngredients')


class Unit(models.Model):
    name = models.CharField()


class Quantity(models.Model):
    amount = models.DecimalField()
    unit = models.ForeignKey(Unit)


class BeverageIngredients(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    beverage = models.ForeignKey(Beverage, on_delete=models.CASCADE)
    quantity = models.ForeignKey(Quantity, on_delete=models.CASCADE)
