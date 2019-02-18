from django.contrib import admin

# Register your models here.
from api.models import Ingredient, Beverage, Unit, Quantity, BeverageIngredients

admin.site.register(Ingredient)
admin.site.register(Beverage)
admin.site.register(Unit)
admin.site.register(Quantity)
admin.site.register(BeverageIngredients)