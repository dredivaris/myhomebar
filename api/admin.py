from django.contrib import admin

# Register your models here.
from api.models import Ingredient, Recipe, Unit, Quantity, RecipeIngredients

admin.site.register(Ingredient)
admin.site.register(Recipe)
admin.site.register(Unit)
admin.site.register(Quantity)
admin.site.register(RecipeIngredients)